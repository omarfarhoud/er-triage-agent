from dataclasses import dataclass
from src.tools.symptom_tool import analyze_symptoms
from src.tools.vital_signs_tool import analyze_vitals


# ── Dataclass ─────────────────────────────────────────────

@dataclass
class DecisionResult:
    final_priority: str
    department: str | None
    explanation: str


# ── Category → Department Mapping ─────────────────────────

CATEGORY_TO_DEPT = {
    "cardiac": "Cardiology",
    "respiratory": "Pulmonology",
    "neuro": "Neurology",
    "trauma": "Emergency",
    "infection": "Internal Medicine",
    "abdominal": "Gastroenterology",
}


# ── Decision Logic ─────────────────────────────────────────

def make_decision(vital_result, symptom_result) -> DecisionResult:
    v_cat = vital_result.risk_category
    s_cat = symptom_result.risk_category

    v_score = vital_result.risk_score
    s_score = symptom_result.risk_score

    dominant = symptom_result.dominant_category

    # ── FINAL PRIORITY ─────────────────────────

    if v_cat == "High Risk" or s_cat == "High Risk":
        final_priority = "HIGH"

    elif v_cat == "Moderate Risk" and s_cat == "Moderate Risk":
        final_priority = "HIGH"

    elif v_cat == "Moderate Risk" or s_cat == "Moderate Risk":
        final_priority = "MODERATE"

    else:
        final_priority = "LOW"

    # ── DEPARTMENT ─────────────────────────────

    if dominant:
        department = CATEGORY_TO_DEPT.get(dominant, "General Medicine")
    else:
        department = "General Medicine"

    # ── IMPROVED EXPLANATION ───────────────────

    reasons = []

    if v_cat == "High Risk":
        reasons.append("critical vital signs detected")
    elif v_cat == "Moderate Risk":
        reasons.append("abnormal vital signs present")

    if s_cat == "High Risk":
        reasons.append("severe symptoms identified")
    elif s_cat == "Moderate Risk":
        reasons.append("moderate symptom severity")

    if dominant:
        reasons.append(f"primary concern in {dominant} system")

    if final_priority == "HIGH":
        reasons.append("immediate attention required")

    explanation = ", ".join(reasons)

    return DecisionResult(
        final_priority=final_priority,
        department=department,
        explanation=explanation,
    )


# ── TEST CASES ───────────────────────────────────────────

if __name__ == "__main__":

    test_cases = [
        {
            "name": "Cardiac Emergency",
            "text": "Severe chest pain and shortness of breath",
            "vitals": {
                "heart_rate": 120,
                "systolic_bp": 85,
                "diastolic_bp": 55,
                "oxygen_saturation": 90,
                "body_temperature": 38
            }
        },
        {
            "name": "Mild Case",
            "text": "Mild headache and fatigue",
            "vitals": {
                "heart_rate": 75,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "oxygen_saturation": 98,
                "body_temperature": 36.8
            }
        },
        {
            "name": "Respiratory Issue",
            "text": "Cough and difficulty breathing",
            "vitals": {
                "heart_rate": 95,
                "systolic_bp": 110,
                "diastolic_bp": 70,
                "oxygen_saturation": 93,
                "body_temperature": 37.5
            }
        },
        {
            "name": "Neurological Emergency",
            "text": "Patient has slurred speech and weakness on one side",
            "vitals": {
                "heart_rate": 88,
                "systolic_bp": 130,
                "diastolic_bp": 85,
                "oxygen_saturation": 97,
                "body_temperature": 37
            }
        },
        {
            "name": "Mixed Moderate Case",
            "text": "Fever, nausea, and cough",
            "vitals": {
                "heart_rate": 102,
                "systolic_bp": 110,
                "diastolic_bp": 75,
                "oxygen_saturation": 95,
                "body_temperature": 38.5
            }
        },
        {
            "name": "Trauma Case",
            "text": "Patient fell and has severe pain and bleeding",
            "vitals": {
                "heart_rate": 110,
                "systolic_bp": 95,
                "diastolic_bp": 60,
                "oxygen_saturation": 96,
                "body_temperature": 37
            }
        }
    ]

    for case in test_cases:
        print("\n" + "=" * 50)
        print(f"Test: {case['name']}")
        print("-" * 50)

        s_result = analyze_symptoms(case["text"])
        v_result = analyze_vitals(case["vitals"])

        decision = make_decision(v_result, s_result)

        print(f"Priority   : {decision.final_priority}")
        print(f"Department : {decision.department}")
        print(f"Explanation: {decision.explanation}")