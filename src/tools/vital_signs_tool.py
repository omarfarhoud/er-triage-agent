# src/tools/vital_signs_tool.py

from dataclasses import dataclass, field

# ── Thresholds (from preprocessing notebook) ──────────────────────────────────

THRESHOLDS = {
    "heart_rate": {
        "critical": 120,
        "warning":  100,
        "unit":     "bpm",
        "inverted": False,
    },
    "oxygen_saturation": {
        "critical": 90,
        "warning":  95,
        "unit":     "%",
        "inverted": True,   # lower is worse
    },
    "body_temperature": {
        "critical": 39.0,
        "warning":  37.5,
        "unit":     "°C",
        "inverted": False,
    },
    "systolic_bp": {
        "critical": 160,
        "warning":  140,
        "unit":     "mmHg",
        "inverted": False,
    },
}

# ── Risk score bands (from preprocessing notebook) ────────────────────────────
# score >= 5 → High Risk
# score >= 3 → Moderate Risk
# else       → Low Risk

# ── Output dataclass ──────────────────────────────────────────────────────────

@dataclass
class FlaggedVital:
    vital:    str
    value:    float
    unit:     str
    severity: str   # "warning" | "critical"
    score:    int


@dataclass
class VitalSignsResult:
    risk_category: str              # "Low Risk" | "Moderate Risk" | "High Risk"
    risk_score:    int
    flagged_vitals: list[FlaggedVital] = field(default_factory=list)
    all_vitals:    dict            = field(default_factory=dict)
    derived:       dict            = field(default_factory=dict)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _score_vital(name: str, value: float) -> tuple[int, str | None]:
    cfg = THRESHOLDS.get(name)
    if cfg is None or value is None:
        return 0, None

    if cfg["inverted"]:
        if value < cfg["critical"]:
            return 2, "critical"
        elif value < cfg["warning"]:
            return 1, "warning"
    else:
        if value > cfg["critical"]:
            return 2, "critical"
        elif value > cfg["warning"]:
            return 1, "warning"

    return 0, None


def _derive(vitals: dict) -> dict:
    sbp = vitals.get("systolic_bp")
    dbp = vitals.get("diastolic_bp")
    derived = {}
    if sbp is not None and dbp is not None:
        derived["MAP"]            = round((sbp + 2 * dbp) / 3, 2)
        derived["pulse_pressure"] = round(sbp - dbp, 2)
    return derived


# ── Main tool function ────────────────────────────────────────────────────────

def analyze_vitals(vitals: dict) -> VitalSignsResult:
    """
    Analyzes patient vital signs and returns a risk assessment.

    Args:
        vitals: dict with keys:
            - heart_rate         (float, bpm)
            - oxygen_saturation  (float, %)
            - body_temperature   (float, °C)
            - systolic_bp        (float, mmHg)
            - diastolic_bp       (float, mmHg)  [used for derived metrics only]

    Returns:
        VitalSignsResult
    """
    total_score  = 0
    flagged      = []

    for vital_name in THRESHOLDS:
        value = vitals.get(vital_name)
        if value is None:
            continue
        score, severity = _score_vital(vital_name, value)
        total_score += score
        if severity:
            flagged.append(FlaggedVital(
                vital    = vital_name,
                value    = value,
                unit     = THRESHOLDS[vital_name]["unit"],
                severity = severity,
                score    = score,
            ))

    if total_score >= 5:
        risk_category = "High Risk"
    elif total_score >= 3:
        risk_category = "Moderate Risk"
    else:
        risk_category = "Low Risk"

    return VitalSignsResult(
        risk_category  = risk_category,
        risk_score     = total_score,
        flagged_vitals = flagged,
        all_vitals     = vitals,
        derived        = _derive(vitals),
    )