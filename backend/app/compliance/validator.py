import json
from pathlib import Path
from typing import Any, Dict, List

from app.compliance.models import ComplianceResult, ComplianceViolation, LayoutExtract

_RULES_PATH = Path(__file__).resolve().parent / "rules" / "us_irc_baseline.json"

DISCLAIMER = (
    "This is an AI-generated design screened against simplified IRC-style thresholds for demonstration only. "
    "It is not legal or code compliance and must be reviewed by a licensed professional before construction."
)


def _load_rules() -> Dict[str, Any]:
    with open(_RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _bedroom_name(name: str) -> bool:
    n = (name or "").lower()
    return "bedroom" in n or n.strip() == "bed"


def _score_band(score: float) -> str:
    if score >= 85:
        return "good"
    if score >= 60:
        return "needs_review"
    return "not_compliant"


def validate_us_irc_baseline(layout: LayoutExtract, raw_for_response: bool = True) -> ComplianceResult:
    """
    Compare extracted layout metrics to MVP IRC baseline thresholds.
    Only rules with sufficient data contribute to applicable_rules / score.
    """
    rules_doc = _load_rules()
    thresholds = rules_doc["thresholds"]
    jid = rules_doc["jurisdiction_id"]
    label = rules_doc["label"]

    violations: List[ComplianceViolation] = []
    passed = 0
    applicable = 0

    # Bedrooms (named bedroom + known area)
    for room in layout.rooms:
        if _bedroom_name(room.name) and room.area_sqft is not None:
            applicable += 1
            min_a = float(thresholds["bedroom_min_area_sqft"])
            if room.area_sqft >= min_a:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="bedroom_min_area",
                        message=f'Bedroom "{room.name}" is {room.area_sqft:.1f} sq ft (minimum {min_a:.0f} sq ft for this screening).',
                        suggestion=f"Increase bedroom area to at least {min_a:.0f} sq ft.",
                    )
                )

    # Ceiling heights (rooms that specify ceiling_ft)
    min_ceiling = float(thresholds["min_ceiling_height_ft"])
    for room in layout.rooms:
        if room.ceiling_ft is not None:
            applicable += 1
            if room.ceiling_ft >= min_ceiling:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="min_ceiling_height",
                        message=f'Room "{room.name}" ceiling height {room.ceiling_ft:.2f} ft is below minimum {min_ceiling:.1f} ft for this screening.',
                        suggestion=f"Increase ceiling height to at least {min_ceiling:.1f} ft.",
                    )
                )

    # Doors
    min_door = float(thresholds["door_min_width_in"])
    for i, door in enumerate(layout.doors_inches):
        if door.width_in is not None:
            applicable += 1
            if door.width_in >= min_door:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="door_min_width",
                        message=f"Door #{i + 1} width {door.width_in:.2f} in is below minimum {min_door:.2f} in.",
                        suggestion=f"Use doors at least {min_door:.0f} in wide where required.",
                    )
                )

    # Stairs — apply checks only when corresponding dimension is known
    if layout.stairs:
        max_rise = float(thresholds["stair_max_rise_in"])
        min_tread = float(thresholds["stair_min_tread_in"])
        if layout.stairs.rise_in is not None:
            applicable += 1
            if layout.stairs.rise_in <= max_rise:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="stair_max_rise",
                        message=f"Stair rise {layout.stairs.rise_in:.2f} in exceeds maximum {max_rise:.2f} in for this screening.",
                        suggestion=f"Reduce rise to no more than {max_rise:.2f} in.",
                    )
                )
        if layout.stairs.tread_in is not None:
            applicable += 1
            if layout.stairs.tread_in >= min_tread:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="stair_min_tread",
                        message=f"Stair tread {layout.stairs.tread_in:.2f} in is below minimum {min_tread:.2f} in.",
                        suggestion=f"Increase tread depth to at least {min_tread:.2f} in.",
                    )
                )

    min_egress = float(thresholds["egress_window_min_area_sqft"])
    for i, win in enumerate(layout.egress_windows_sqft):
        if win.area_sqft is not None:
            applicable += 1
            if win.area_sqft >= min_egress:
                passed += 1
            else:
                violations.append(
                    ComplianceViolation(
                        rule_id="egress_window_min_area",
                        message=f"Egress opening #{i + 1} net clear area {win.area_sqft:.2f} sq ft is below minimum {min_egress:.2f} sq ft for this screening.",
                        suggestion=f"Increase egress opening to at least {min_egress:.2f} sq ft clear.",
                    )
                )

    suggestions = list(dict.fromkeys(v.suggestion for v in violations))

    if applicable == 0:
        return ComplianceResult(
            jurisdiction_id=jid,
            jurisdiction_label=label,
            score_percent=None,
            status_label="insufficient_data",
            passed_rules=0,
            applicable_rules=0,
            violations=[],
            suggestions=[
                "No measurable dimensions were extracted for IRC screening. Try a more explicit prompt with feet/inches or dimensions."
            ],
            disclaimer=DISCLAIMER,
            layout_extract=layout.model_dump() if raw_for_response else None,
        )

    score = (passed / applicable) * 100.0
    status = _score_band(score)

    return ComplianceResult(
        jurisdiction_id=jid,
        jurisdiction_label=label,
        score_percent=round(score, 1),
        status_label=status,
        passed_rules=passed,
        applicable_rules=applicable,
        violations=violations,
        suggestions=suggestions,
        disclaimer=DISCLAIMER,
        layout_extract=layout.model_dump() if raw_for_response else None,
    )


def parse_layout_from_llm_dict(data: Dict[str, Any]) -> LayoutExtract:
    """Coerce arbitrary JSON dict from Gemini into LayoutExtract."""
    if not isinstance(data, dict):
        return LayoutExtract()
    return LayoutExtract.model_validate(data)
