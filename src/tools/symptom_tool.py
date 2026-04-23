# src/tools/symptom_understanding_tool.py

import re
from dataclasses import dataclass, field

# ── Pattern Map ───────────────────────────────────────────────────────────────
# Each concept has one compiled regex that matches any of its variants.
# Negated matches (no/not/without/denies...) leave group 1 empty → not flagged.
# Real matches set group 1 → flagged.
# score: 2 = critical  |  1 = warning

def _p(*terms):
    """
    Build a compiled, case-insensitive OR pattern where:
    - negation prefix + term  →  match with group 1 = None  (ignored)
    - bare term               →  match with group 1 = term   (flagged)
    Word boundary \\b is applied per term so multi-word phrases work correctly.
    """
    parts = "|".join(rf"\b{t}" for t in terms)
    neg   = r"(?:no|not|without|denies?|absence of|negative for)\s{1,30}"
    return re.compile(rf"{neg}(?:{parts})|({parts})", re.I)
HIGH_PRIORITY_SYMPTOMS = {
    "cardiac_arrest",   # 🚨 life-threatening
    "focal_deficit",    # stroke
    "bleeding",         # hemorrhage
    "dyspnea",          # respiratory distress
}
SYMPTOMS = {
    # cardiac
    "chest_pain":      {"category": "cardiac",     "severity": "critical", "score": 2,
                        "pattern": _p("chest pain", "chest tightness", "chest pressure", "angina")},
    "syncope": {
        "category": "cardiac",
        "severity": "critical",
        "score": 2,
        "pattern": _p("syncope", "fainted", "fainting", "loss of consciousness", "passed out")
    },

    "cardiac_arrest": {
        "category": "cardiac",
        "severity": "critical",
        "score": 2,
        "pattern": _p("cardiac arrest")
    },
    "palpitations":    {"category": "cardiac",     "severity": "warning",  "score": 1,
                        "pattern": _p("palpitat", "irregular heartbeat", "heart racing", "arrhythmia", "atrial fibrillation")},
    "edema":           {"category": "cardiac",     "severity": "warning",  "score": 1,
                        "pattern": _p("edema", "peripheral swelling", "bilateral swelling", "leg swelling", "ankle swelling")},
    "cardiac_disease": {"category": "cardiac",     "severity": "warning",  "score": 1,
                        "pattern": _p("heart failure", "valve", "coronary", "myocardial", "ventricular", "cardiomyopath")},

    # respiratory
    "dyspnea":         {"category": "respiratory", "severity": "critical", "score": 2,
                        "pattern": _p("dyspnea", "shortness of breath", "difficulty breathing", "breathless", "respiratory distress")},
    "hypoxia":         {"category": "respiratory", "severity": "critical", "score": 2,
                        "pattern": _p("hypoxia", "hypoxemia", "cyanosis", "cyanotic", "low oxygen")},
    "cough":           {"category": "respiratory", "severity": "warning",  "score": 1,
                        "pattern": _p("cough", "hemoptysis", "wheezing", "stridor")},
    # added: covers pulmonary/pleural findings common in missed respiratory cases
    "pulmonary_signs": {"category": "respiratory", "severity": "warning",  "score": 1,
                        "pattern": _p("pulmonary", "pleural", "lung tumor", "lung mass", "asthma", "pneumothorax")},

    # neuro
    "altered_consciousness": {"category": "neuro", "severity": "critical", "score": 2,
                              "pattern": _p("altered consciousness", "altered mental status", "confusion", "unresponsive", r"gcs\b", "glasgow coma")},
    "seizure":         {"category": "neuro",       "severity": "critical", "score": 2,
                        "pattern": _p("seizure", "convulsion", "epilep", r"tonic.clonic", "status epilepticus")},
    "focal_deficit":   {"category": "neuro",       "severity": "critical", "score": 2,
                        "pattern": _p("hemiplegia", "hemiparesis", "facial droop", "aphasia", "dysarthria","slurred speech", "one-sided weakness",
                                      "weakness on one side", r"stroke\b", "transient ischemic")},
    "headache":        {"category": "neuro",       "severity": "warning",  "score": 1,
                        "pattern": _p("headache", "migraine", "cephalgia")},
    # added: nerve/spinal involvement
    "nerve_deficit":   {"category": "neuro",       "severity": "warning",  "score": 1,
                        "pattern": _p("nerve", "spinal", "neuropath", "radiculopath", "myelopath")},
    # added: motor/sensory symptoms
    "motor_sensory":   {"category": "neuro",       "severity": "warning",  "score": 1,
                        "pattern": _p("weakness", "numbness", "paresthesia", "ataxia", "palsy", "vertigo", "tremor")},

    # infection
    "sepsis":          {"category": "infection",   "severity": "critical", "score": 2,
                        "pattern": _p("sepsis", "septic shock", "bacteremia", "systemic infection", "hypotension"        ,"systemic inflammatory")},
    "fever":           {"category": "infection",   "severity": "warning",  "score": 1,
                        "pattern": _p("fever", "febrile", "pyrexia", "hyperthermia", "leukocytosis", "elevated crp")},
    "infection_site":  {"category": "infection",   "severity": "warning",  "score": 1,
                        "pattern": _p("pneumonia", "urinary tract infection", "meningitis", "cellulitis", "abscess", "endocarditis")},
    # added: inflammatory/microbial markers common in missed infection cases
    "pathogen_signs":  {"category": "infection",   "severity": "warning",  "score": 1,
                        "pattern": _p("inflammatory", "bacterial", "viral", "fungal", "infectious")},

    # trauma
    "bleeding":        {"category": "trauma",      "severity": "critical", "score": 2,
                        "pattern": _p("hemorrhage", "hematemesis", "melena", "hematuria", "bleeding", "blood loss", "epistaxis")},
    "acute_pain":      {"category": "trauma",      "severity": "critical", "score": 2,
                        "pattern": _p("severe pain", "acute pain", "excruciating", r"10/10")},
    # added: rupture and posttraumatic to injury
    "injury":          {"category": "trauma",      "severity": "warning",  "score": 1,
                        "pattern": _p("fracture", "dislocation", "laceration", "contusion", "blunt trauma",  "fall",   "fell",  "fall from", "rupture", "posttraumatic")},
    "nausea_vomiting": {
        "category": "abdominal",
        "severity": "warning",
        "score": 1,
        "pattern": _p("nausea", "vomiting", "emesis")
    },
    "abdominal_pain": {
        "category": "abdominal",
        "severity": "critical",
        "score": 2,
        "pattern": _p("abdominal pain", "stomach pain", "epigastric pain")
    }
}

# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class FlaggedSymptom:
    symptom:  str
    category: str
    severity: str   # "warning" | "critical"
    score:    int


@dataclass
class SymptomResult:
    risk_category:     str
    risk_score:        int
    dominant_category: str | None
    flagged_symptoms:  list[FlaggedSymptom] = field(default_factory=list)


# ── Main tool ─────────────────────────────────────────────────────────────────

def analyze_symptoms(text: str) -> SymptomResult:
    total_score = 0
    flagged = []
    category_scores: dict[str, int] = {}

    for symptom_name, cfg in SYMPTOMS.items():
        m = cfg["pattern"].search(text)
        if m and m.group(1):    # group 1 set = real match (not negated)
            total_score += cfg["score"]
            category_scores[cfg["category"]] = category_scores.get(cfg["category"], 0) + cfg["score"]
            flagged.append(FlaggedSymptom(
                symptom=symptom_name,
                category=cfg["category"],
                severity=cfg["severity"],
                score=cfg["score"],
            ))

    has_critical = any(s.severity == "critical" for s in flagged)
    dominant = max(category_scores, key=category_scores.get) if category_scores else None

    # 🚨 Override: certain symptoms are automatically high risk
    has_high_priority = any(
        f.symptom in HIGH_PRIORITY_SYMPTOMS for f in flagged
    )

    if has_high_priority or total_score >= 5:
        risk_category = "High Risk"
    elif total_score >= 3 or has_critical:
        risk_category = "Moderate Risk"
    else:
        risk_category = "Low Risk"
    return SymptomResult(
        risk_category=risk_category,
        risk_score=total_score,
        dominant_category=dominant,
        flagged_symptoms=flagged,
    )


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        # 1️⃣ Negation (VERY IMPORTANT)
        {"name": "Negation Cardiac",
         "text": "Patient denies chest pain and denies shortness of breath."},

        # 2️⃣ Negation mixed
        {"name": "Negation Mixed",
         "text": "No fever but severe headache and dizziness present."},

        # 3️⃣ Hidden stroke wording
        {"name": "Stroke (Indirect)",
         "text": "Patient presents with slurred speech and weakness on one side."},

        # 4️⃣ Severe infection without explicit 'sepsis'
        {"name": "Severe Infection Implicit",
         "text": "High fever with hypotension and signs of systemic infection."},

        # 5️⃣ Cardiac + respiratory conflict
        {"name": "Cardio-Respiratory",
         "text": "Chest tightness with shortness of breath and wheezing."},

        # 6️⃣ Only mild symptoms
        {"name": "Mild General Case",
         "text": "Patient complains of fatigue and mild headache."},

        # 7️⃣ Multiple warnings → aggregation
        {"name": "Multiple Warning Symptoms",
         "text": "Fever, cough, and nausea for two days."},

        # 8️⃣ Trauma without explicit keywords
        {"name": "Hidden Trauma",
         "text": "Patient fell from a ladder and has severe pain."},

        # 9️⃣ Trauma + neuro (critical mix)
        {"name": "Trauma + Neuro",
         "text": "After a fall, patient is unresponsive with altered consciousness."},

        # 🔟 Respiratory but mild
        {"name": "Mild Respiratory",
         "text": "Slight cough and mild wheezing."},

        # 11️⃣ Hypoxia only (high priority)
        {"name": "Hypoxia Only",
         "text": "Patient cyanotic with low oxygen saturation."},

        # 12️⃣ Bleeding without trauma context
        {"name": "Internal Bleeding",
         "text": "Patient has melena and signs of blood loss."},

        # 13️⃣ Conflicting categories
        {"name": "Neuro + Infection",
         "text": "Fever with confusion and altered mental status."},

        # 14️⃣ Abdominal but non-critical
        {"name": "Mild Abdominal",
         "text": "Patient has nausea without abdominal pain."},

        # 15️⃣ Extreme multi-system
        {"name": "Multi-System Critical",
         "text": "Chest pain, shortness of breath, hemiplegia, and severe bleeding."},
    ]

    for case in test_cases:
        print("\n" + "=" * 50)
        print(f"Test: {case['name']}")
        print("-" * 50)

        result = analyze_symptoms(case["text"])

        print(f"Risk Category    : {result.risk_category}")
        print(f"Risk Score       : {result.risk_score}")
        print(f"Dominant Category: {result.dominant_category}")

        print("\nFlagged Symptoms:")
        for s in result.flagged_symptoms:
            print(f"  - {s.symptom} [{s.category}] ({s.severity}, +{s.score})")
        if not result.flagged_symptoms:
            print("  - None")