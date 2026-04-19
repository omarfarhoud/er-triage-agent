# src/tools/vital_signs_tool.py

from dataclasses import dataclass, field

# ── Thresholds ───────────────────────────────────────────────────────────────

THRESHOLDS = {
    "heart_rate": {
        "critical_high": 120,
        "warning_high":  100,
        "critical_low":  50,
        "warning_low":   60,
        "unit":          "bpm",
    },
    "oxygen_saturation": {
        "critical_low": 90,
        "warning_low":  95,
        "unit":         "%",
    },
    "body_temperature": {
        "critical_high": 39.0,
        "warning_high":  37.5,
        "critical_low":  35.0,
        "warning_low":   36.0,
        "unit":          "°C",
    },
    "systolic_bp": {
        "critical_high": 160,
        "warning_high":  140,
        "critical_low": 90,
        "warning_low": 100,
        "unit":          "mmHg",
    },
    "diastolic_bp": {
        "critical_high": 100,
        "warning_high":  90,
        "critical_low":  60,
        "warning_low":   70,
        "unit":          "mmHg",
    },
    "MAP": {
        "critical_low": 65,
        "warning_low":  70,
        "unit":         "mmHg",
    }
}

# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class FlaggedVital:
    vital:    str
    value:    float
    unit:     str
    severity: str   # "warning" | "critical"
    score:    int


@dataclass
class VitalSignsResult:
    risk_category: str
    risk_score:    int
    flagged_vitals: list[FlaggedVital] = field(default_factory=list)
    all_vitals:    dict = field(default_factory=dict)
    derived:       dict = field(default_factory=dict)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _score_vital(name: str, value: float) -> tuple[int, str | None]:
    cfg = THRESHOLDS.get(name)
    if cfg is None or value is None:
        return 0, None

    # HIGH side
    if "critical_high" in cfg and value > cfg["critical_high"]:
        return 2, "critical"
    if "warning_high" in cfg and value > cfg["warning_high"]:
        return 1, "warning"

    # LOW side
    if "critical_low" in cfg and value < cfg["critical_low"]:
        return 2, "critical"
    if "warning_low" in cfg and value < cfg["warning_low"]:
        return 1, "warning"

    return 0, None


def _derive(vitals: dict) -> dict:
    sbp = vitals.get("systolic_bp")
    dbp = vitals.get("diastolic_bp")
    derived = {}

    if sbp is not None and dbp is not None:
        derived["MAP"] = round((sbp + 2 * dbp) / 3, 2)
        derived["pulse_pressure"] = round(sbp - dbp, 2)

    return derived


# ── Main tool ───────────────────────────────────────────────────────────────

def analyze_vitals(vitals: dict) -> VitalSignsResult:
    total_score = 0
    flagged = []

    # Score original vitals
    for vital_name in ["heart_rate", "oxygen_saturation", "body_temperature", "systolic_bp","diastolic_bp"]:
        value = vitals.get(vital_name)
        if value is None:
            continue

        score, severity = _score_vital(vital_name, value)
        total_score += score

        if severity:
            flagged.append(FlaggedVital(
                vital=vital_name,
                value=value,
                unit=THRESHOLDS[vital_name]["unit"],
                severity=severity,
                score=score,
            ))

    # ── NEW: score MAP (diastolic now matters indirectly) ──
    derived = _derive(vitals)
    map_value = derived.get("MAP")

    if map_value is not None:
        score, severity = _score_vital("MAP", map_value)
        total_score += score

        if severity:
            flagged.append(FlaggedVital(
                vital="MAP",
                value=map_value,
                unit="mmHg",
                severity=severity,
                score=score,
            ))

    # Risk classification
    has_critical = any(v.severity == "critical" for v in flagged)

    if total_score >= 5:
        risk_category = "High Risk"
    elif total_score >= 3 or has_critical:
        risk_category = "Moderate Risk"
    else:
        risk_category = "Low Risk"

    return VitalSignsResult(
        risk_category=risk_category,
        risk_score=total_score,
        flagged_vitals=flagged,
        all_vitals=vitals,
        derived=derived,
    )

if __name__ == "__main__":
    test_cases = [
        {
            "name": "Normal Case",
            "vitals": {
                "heart_rate": 75,
                "oxygen_saturation": 98,
                "body_temperature": 36.8,
                "systolic_bp": 120,
                "diastolic_bp": 80,
            },
        },
        {
            "name": "Low BP (Shock via MAP)",
            "vitals": {
                "heart_rate": 110,
                "oxygen_saturation": 94,
                "body_temperature": 37.0,
                "systolic_bp": 80,
                "diastolic_bp": 50,
            },
        },
        {
            "name": "Bradycardia (Low HR)",
            "vitals": {
                "heart_rate": 45,
                "oxygen_saturation": 98,
                "body_temperature": 36.5,
                "systolic_bp": 120,
                "diastolic_bp": 80,
            },
        },
        {
            "name": "Hypothermia",
            "vitals": {
                "heart_rate": 70,
                "oxygen_saturation": 98,
                "body_temperature": 34.5,
                "systolic_bp": 120,
                "diastolic_bp": 80,
            },
        },
        {
            "name": "High Risk (Multiple Critical)",
            "vitals": {
                          "heart_rate": 75,
                          "oxygen_saturation": 98,
                          "body_temperature": 36.8,
                          "systolic_bp": 70,
                          "diastolic_bp": 40,
                      },


        },
    ]

    for case in test_cases:
        print("\n" + "="*50)
        print(f"Test: {case['name']}")
        print("-"*50)

        result = analyze_vitals(case["vitals"])

        print(f"Risk Category: {result.risk_category}")
        print(f"Risk Score: {result.risk_score}")
        print(f"Derived: {result.derived}")

        print("\nFlagged Vitals:")
        for v in result.flagged_vitals:
            print(f" - {v.vital}: {v.value} {v.unit} ({v.severity}, +{v.score})")

        if not result.flagged_vitals:
            print(" - None")