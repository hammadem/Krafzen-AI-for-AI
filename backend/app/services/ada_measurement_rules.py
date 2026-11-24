"""Evidence-based, narrowly scoped ADA 2010 numerical measurement checks.

Official 2010 ADA Standards narrow numerical rules, with opt-in extended checks.
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

    # Additional independent numeric checks are opt-in; old saved screenings
    # retain their original scope. A qualified reviewer must first confirm
    # that these ordinary element types apply and special exceptions are absent.
    if measurements.get("extended_checks") is True:
        scope_ready = base_ready and measurements.get("extended_scope_confirmed") is True
        definitions = [
            ("304.3.1","circular_turn_diameter_in","Circular turning-space diameter only",60.0,"in","min"),
            ("305.3","clear_floor_width_in","Clear floor space width only",30.0,"in","min"),
            ("305.3","clear_floor_length_in","Clear floor space length only",48.0,"in","min"),
            ("403.3","walking_running_slope_pct","Ordinary accessible walking surface running slope",5.0,"%","max"),
            ("403.3","walking_cross_slope_pct","Ordinary accessible walking surface cross slope",100/48,"%","max"),
            ("405.5","ramp_run_clear_width_in","Ramp run clear width between handrails, where present",36.0,"in","min"),
            ("405.6","ramp_single_run_rise_in","Rise of a single ordinary ramp run",30.0,"in","max"),
            ("405.7.3","ramp_landing_clear_length_in","Ordinary ramp landing clear length only",60.0,"in","min"),
        ]
        for section,key,description,threshold,unit,direction in definitions:
            raw=measurements.get(key)
            measured=_measurement(raw)
            if unit=="%" and isinstance(raw,(int,float)) and not isinstance(raw,bool) and raw==0:
                measured=0.0
            if not scope_ready or measured is None:
                status="unknown"
                reason="Measurement, edition, applicability or ordinary-element scope and exceptions have not been confirmed."
            else:
                passed=(measured>=threshold if direction=="min" else measured<=threshold+1e-12)
                status="pass" if passed else "fail"
                reason=f"Declared value {measured:.4g} {unit} {'meets' if passed else 'does not meet'} the selected numerical threshold. All other element conditions remain unassessed."
            append(rule_id="ADA-"+section+"-"+key,section=section,description=description,
                expected=threshold,measured=measured,basis=f"{direction} threshold {threshold:.8g} {unit}",
                unit=unit,prerequisites=[key,"extended_scope_confirmed"],status=status,reason=reason)

    counts = {
        state: sum(1 for row in findings if row["result"] == state)
        for state in ("pass", "fail", "unknown")
    }
    missing = sorted({
        field for finding in findings if finding["result"] == "unknown"
        for field in finding["required_inputs"]
        if measurements.get(field) is None and context.get(field) is None
    })
    if measurements.get("extended_checks") is True and measurements.get("extended_scope_confirmed") is not True:
        missing.append("extended ordinary-element applicability and exceptions confirmed")
    if not edition_supported:
        missing.append("supported standard_edition=2010_ADA")
    if not applicability:
        missing.append("ADA applicability confirmed by qualified reviewer")
    if not all(jurisdiction.values()):
        missing.extend(k for k, v in jurisdiction.items() if not v)

    return {
        "standard": "2010 ADA Standards for Accessible Design",
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
