"""Evidence-based, narrowly scoped ADA 2010 numerical measurement checks.

Only official 2010 ADA Standards sections 404.2.3, 403.5.1 and 405.2, with optional 405.3, 405.5 and 405.6.
This module does NOT determine which standards apply to a project, nor does
passing a threshold establish code compliance, approval or professional review.
Unknown edition/applicability/exception/measurement -> UNKNOWN, never PASS.
"""
from datetime import UTC, datetime
from math import isfinite
from typing import Any

OFFICIAL_SOURCE = "https://www.ada.gov/law-and-regs/design-standards/2010-stds/"


def _measurement(raw: Any) -> float | None:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    value = float(raw)
    return value if isfinite(value) and value > 0 else None


def evaluate_ada_measurements(
    *, context: dict[str, Any], measurements: dict[str, Any],
) -> dict[str, Any]:
    """Return traceable per-rule numerical results, never a compliance approval."""
    jurisdiction = {
        "state": str(context.get("state") or "").strip(),
        "municipality": str(context.get("municipality") or "").strip(),
        "occupancy": str(context.get("occupancy") or "").strip(),
        "building_type": str(context.get("building_type") or "").strip(),
        "project_address": str(context.get("project_address") or "").strip(),
        "standard_edition": str(context.get("standard_edition") or "").strip(),
    }
    edition_supported = jurisdiction["standard_edition"] == "2010_ADA"
    applicability = context.get("ada_applicability_confirmed") is True
    base_ready = (
        edition_supported and applicability and
        all(jurisdiction[k] for k in (
            "state", "municipality", "occupancy", "building_type",
            "project_address",
        ))
    )
    findings = []

    def append(
        *, rule_id: str, section: str, description: str,
        expected: float | None, measured: float | None,
        basis: str, unit: str, prerequisites: list[str],
        status: str, reason: str,
    ) -> None:
        findings.append({
            "rule_id": rule_id,
            "code_family": "ADA",
            "edition": "2010",
            "section_reference": section,
            "jurisdiction": jurisdiction,
            "applicability_declared": applicability,
            "source_url": OFFICIAL_SOURCE,
            "measurement_scope": description,
            "required_inputs": prerequisites,
            "calculation_method": basis,
            "threshold": expected,
            "measured": measured,
            "unit": unit,
            "result": status,
            "severity": "review_required" if status != "pass" else "informational",
            "evidence": {
                "type": "user_declared_measurement",
                "automatically_extracted_from_model": False,
                "field_verified": False,
            },
            "explanation": reason,
            "suggested_action": (
                "Obtain the missing values, applicable exceptions and reviewer "
                "confirmation before any code conclusion."
                if status == "unknown" else
                "Review measured condition with a qualified accessibility professional."
            ),
        })

    # ADA §404.2.3, restricted to the measured clear width of manual swinging
    # doors; actual 90-degree clear opening and doorway depth are required.
    door = _measurement(measurements.get("door_clear_width_in"))
    depth = _measurement(measurements.get("doorway_depth_in"))
    swinging = measurements.get("door_kind") == "manual_swinging"
    measured_90 = measurements.get("door_measured_at_90_degrees") is True
    door_fields = [
        "door_clear_width_in", "doorway_depth_in", "door_kind",
        "door_measured_at_90_degrees", "ada_applicability_confirmed",
    ]
    if not base_ready or door is None or depth is None or not swinging or not measured_90:
        append(
            rule_id="ADA-404.2.3-clear-width",
            section="404.2.3",
            description="Manual swinging door clear opening width only",
            expected=None, measured=door, basis="threshold based on doorway depth",
            unit="in", prerequisites=door_fields, status="unknown",
            reason="Edition, applicability, jurisdiction, 90-degree measurement, door type, depth or width is not verified.",
        )
    else:
        threshold = 36.0 if depth > 24.0 else 32.0
        passed = door >= threshold
        append(
            rule_id="ADA-404.2.3-clear-width",
            section="404.2.3",
            description="Manual swinging door clear opening width only; projections and other door conditions not checked",
            expected=threshold, measured=door,
            basis=f"doorway_depth_in={depth} >24 requires 36in, otherwise 32in",
            unit="in", prerequisites=door_fields,
            status="pass" if passed else "fail",
            reason=f"Declared clear width {door:.2f}in {'meets' if passed else 'is below'} "
                   f"the narrow section 404.2.3 width threshold of {threshold:.0f}in; "
                   "door projections, hardware, maneuvering clearances and exceptions remain unverified.",
        )

    # ADA §403.5.1 nominal accessible route minimum 36 inches; an exception
    # permits some short reductions and the check must be UNKNOWN if relevant.
    route = _measurement(measurements.get("accessible_route_clear_width_in"))
    exception = measurements.get("route_exception_applies")
    route_fields = ["accessible_route_clear_width_in", "route_exception_applies"]
    if not base_ready or route is None or exception is not False:
        append(
            rule_id="ADA-403.5.1-route-clear-width",
            section="403.5.1",
            description="Nominal accessible walking-surface minimum width only",
            expected=36.0, measured=route, unit="in",
            basis="clear width >=36in when no allowable exception applies",
            prerequisites=route_fields, status="unknown",
            reason="Applicability, measurement or short-segment exception was not ruled out.",
        )
    else:
        passed = route >= 36
        append(
            rule_id="ADA-403.5.1-route-clear-width",
            section="403.5.1",
            description="Nominal accessible walking-surface minimum width only",
            expected=36.0, measured=route, unit="in",
            basis="clear width >=36in with no exception",
            prerequisites=route_fields,
            status="pass" if passed else "fail",
            reason=f"Declared walking surface clear width {route:.2f}in "
                   f"{'meets' if passed else 'is below'} the 36in minimum; "
                   "turning, passing, protrusions and other route requirements are unassessed.",
        )

    # ADA §405.2 new construction ramp running slope max 1:12; different
    # alteration exceptions need qualified interpretation, not automatic pass.
    rise = _measurement(measurements.get("ramp_rise_in"))
    run = _measurement(measurements.get("ramp_horizontal_run_in"))
    ramp_exception = measurements.get("ramp_alteration_exception_applies")
    new_construction = measurements.get("new_construction") is True
    ramp_fields = [
        "ramp_rise_in", "ramp_horizontal_run_in",
        "new_construction", "ramp_alteration_exception_applies",
    ]
    if (not base_ready or rise is None or run is None or
        ramp_exception is not False or not new_construction):
        append(
            rule_id="ADA-405.2-ramp-running-slope",
            section="405.2",
            description="New-construction ramp running slope only",
            expected=1 / 12, measured=rise / run if rise and run else None,
            unit="rise/run", prerequisites=ramp_fields,
            basis="running slope <=1/12",
            status="unknown",
            reason="New-construction applicability, actual rise/run or exception status is unverified.",
        )
    else:
        value = rise / run
        passed = value <= 1 / 12 + 1e-12
        append(
            rule_id="ADA-405.2-ramp-running-slope",
            section="405.2",
            description="New-construction ramp running slope only",
            expected=1 / 12, measured=value,
            unit="rise/run", prerequisites=ramp_fields,
            basis="running slope = rise divided by horizontal run; <=1/12",
            status="pass" if passed else "fail",
            reason=f"Declared ramp slope {value:.5f} "
                   f"{'meets' if passed else 'exceeds'} 1:12 maximum; "
                   "landings, clear width, handrails, cross slope and total rise are unassessed.",
        )

    # Optional expanded screening preserves the legacy three-rule contract
    # for existing clients. Section 405 applicability and exceptions must be
    # established for this particular run (not a curb ramp or a gangway).
    if measurements.get("extended_ramp_checks") is True:
        confirmed = measurements.get("ramp_run_405_applies_no_exception_confirmed") is True
        ramp_ready = base_ready and confirmed and new_construction and ramp_exception is False
        cross_raw = measurements.get("ramp_cross_slope_percent")
        cross = (float(cross_raw) if isinstance(cross_raw, (int, float))
                 and not isinstance(cross_raw, bool) and isfinite(cross_raw)
                 and 0 <= cross_raw <= 100 else None)
        width = _measurement(measurements.get("ramp_clear_width_in"))
        shared = ["ramp_run_405_applies_no_exception_confirmed", "new_construction",
                  "ramp_alteration_exception_applies", "ada_applicability_confirmed"]
        for section, suffix, label, key, value, threshold, unit, minimum in (
            ("405.3", "cross-slope", "Ramp run transverse cross slope", "ramp_cross_slope_percent", cross, 100 / 48, "%", False),
            ("405.5", "clear-width", "Ramp run clear width, between handrails where present", "ramp_clear_width_in", width, 36.0, "in", True),
            ("405.6", "rise", "Vertical rise of a single ramp run", "ramp_rise_in", rise, 30.0, "in", False),
        ):
            if not ramp_ready or value is None:
                status = "unknown"
                reason = "Section 405 applicability, absence of relevant exceptions, new construction or measured value has not been established."
            else:
                passed = value >= threshold if minimum else value <= threshold
                status = "pass" if passed else "fail"
                reason = (f"Declared {label.lower()} {value:.4f} {unit} "
                          f"{'meets' if passed else 'does not meet'} the narrow numerical threshold "
                          f"of {threshold:.6g} {unit}. Other ramp requirements remain unassessed.")
            append(rule_id=f"ADA-{section}-{suffix}", section=section,
                   description=label + " only", expected=threshold, measured=value,
                   basis="minimum measured value" if minimum else
                         ("cross slope percent = 100 × transverse rise/run; maximum 100/48" if section == "405.3" else "maximum measured value"),
                   unit=unit, prerequisites=[key, *shared], status=status, reason=reason)

    counts = {
        state: sum(1 for row in findings if row["result"] == state)
        for state in ("pass", "fail", "unknown")
    }
    missing = sorted({
        field for finding in findings if finding["result"] == "unknown"
        for field in finding["required_inputs"]
        if measurements.get(field) is None and context.get(field) is None
    })
    if not edition_supported:
        missing.append("supported standard_edition=2010_ADA")
    if not applicability:
        missing.append("ADA applicability confirmed by qualified reviewer")
    if not all(jurisdiction.values()):
        missing.extend(k for k, v in jurisdiction.items() if not v)

    return {
        "standard": "2010 ADA Standards for Accessible Design",
        "rule_version": "ada_measurements_v2" if measurements.get("extended_ramp_checks") is True else "ada_measurements_v1",
        "standard_source_url": OFFICIAL_SOURCE,
        "jurisdiction": jurisdiction,
        "source_kind": "user_declared_measurements",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": "pending_qualified_review",
        "numeric_checks_only": True,
        "verified_against_drawing_geometry": False,
        "complete_code_compliance_determined": False,
        "rule_results": findings,
        "counts": counts,
        "missing_information": sorted(set(missing)),
        "disclaimer": (
            "These are isolated numeric thresholds for self-declared values only. "
            "Passing a check is NOT a finding of ADA/IBC/NFPA compliance. "
            "Applicability, exceptions, construction facts, relevant amendments, "
            "additional requirements and code editions require review by a qualified professional."
        ),
    }
