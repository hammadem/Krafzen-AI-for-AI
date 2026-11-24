"""Deterministic, edition-bound building/life-safety measurement rules.

Only individually verified numerical provisions are encoded. A selected model
code is not evidence of local adoption. Every result retains inputs, edition,
section, applicability and evidence. Unsupported categories remain UNKNOWN.
"""
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite

IBC_SOURCE = "https://codes.iccsafe.org/content/IBC2024V2.0/chapter-10-means-of-egress"
NFPA_SOURCE = "https://www.nfpa.org/codes-and-standards/nfpa-101-standard-development/101"
NFPA_CORROBORATION = "https://integratedlightingcampaign.energy.gov/sites/default/files/2024-10/LED%20and%20Controls%20Guidance%20for%20GSA_0.pdf"

COVERAGE = {
    "IBC": (
        "occupancy_classification", "building_area", "building_height",
        "construction_type", "means_of_egress", "exit_access", "exit_capacity",
        "exit_arrangement", "travel_distance", "corridors", "fire_resistance",
        "fire_separation", "fire_protection_systems", "accessibility", "other_building_safety",
    ),
    "NFPA 101": (
        "fire_protection", "fire_alarm", "sprinklers", "fire_extinguishers",
        "emergency_lighting", "exit_signage", "means_of_egress", "fire_doors",
        "fire_separation", "electrical_life_safety",
    ),
}


def _number(value, *, zero_allowed=False):
    if type(value) not in (int, float) or not isfinite(value):
        return None
    if value < 0 or (value == 0 and not zero_allowed) or value > 1e9:
        return None
    return Decimal(str(value))


def evaluate_building_code_measurements(*, context, measurements, source_file_id):
    """Run supported calculations; never infer adoption, exceptions or measurements."""
    context_fields = (
        "state", "municipality", "project_address", "occupancy", "building_type",
        "construction_type", "adoption_reference", "reviewer_name",
    )
    context_ready = (
        all(isinstance(context.get(k), str) and context[k].strip() for k in context_fields)
        and _number(context.get("building_height_ft")) is not None
        and _number(context.get("building_area_sqft")) is not None
        and context.get("local_amendments_reviewed_no_conflict") is True
        and bool(source_file_id)
    )
    findings = []
    enabled = {
        "IBC": context_ready and context.get("ibc_edition") == "2024"
        and context.get("ibc_applicability_confirmed") is True,
        "NFPA 101": context_ready and context.get("nfpa101_edition") == "2024"
        and context.get("nfpa101_applicability_confirmed") is True,
    }

    def emit(family, category, rule_id, section, threshold, actual, unit,
             calculation, fields, eligible, direction="min"):
        # No decimal comparisons until applicability and data are established.
        known = enabled[family] and eligible and actual is not None and threshold is not None
        status = "unknown"
        if known:
            passed = actual >= threshold if direction == "min" else actual <= threshold
            status = "pass" if passed else "fail"
        reason = (
            "Applicable edition, jurisdiction, amendments, evidence or measured inputs remain unconfirmed."
            if not known else
            f"Declared measured value {actual} {unit} {'meets' if status == 'pass' else 'does not meet'} "
            f"this isolated {'minimum' if direction == 'min' else 'maximum'} of {threshold} {unit}."
        )
        findings.append({
            "rule_id": rule_id, "code_family": family, "edition": "2024",
            "section_reference": section, "category": category,
            "jurisdiction": context,
            "source_url": IBC_SOURCE if family == "IBC" else NFPA_SOURCE,
            "supporting_reference_url": NFPA_CORROBORATION if family == "NFPA 101" else IBC_SOURCE,
            "required_inputs": fields, "calculation_method": calculation,
            "threshold": float(threshold) if threshold is not None else None,
            "measured": float(actual) if actual is not None else None, "unit": unit,
            "result": status, "severity": "review_required" if status != "pass" else "informational",
            "evidence": {"type": "user_declared_measurements", "source_file_id": source_file_id,
                         "independently_verified": False,
                         "reviewer_name_asserted": context.get("reviewer_name")},
            "explanation": reason,
            "suggested_action": "Have a qualified reviewer confirm adoption, applicability, exceptions and the source measurements; review and resolve any failed threshold.",
        })

    # Section 1005.3 concerns capacity only, not all minimum widths or egress
    # provisions. The reviewer must establish the applicable factor, and that
    # the special assembly-seating/other exceptions do not control.
    basis = measurements.get("egress_factor_basis")
    occupancy_group = str(context.get("occupancy") or "").strip().upper()
    standard = basis == "standard_confirmed"
    reduced = (
        basis == "sprinkler_voice_exception_confirmed"
        and occupancy_group in {"A-1", "A-2", "A-3", "A-4", "A-5", "B", "E",
                                "F-1", "F-2", "I-1", "I-3", "I-4", "M", "R-1",
                                "R-2", "R-3", "R-4", "S-1", "S-2", "U"}
        and measurements.get("qualifying_sprinkler_system_confirmed") is True
        and measurements.get("qualifying_voice_alarm_confirmed") is True
    )
    applicable = (standard or reduced) and measurements.get("other_egress_exceptions_excluded") is True
    for key, section, normal, exception in (
        ("stair", "1005.3.1", "0.3", "0.2"),
        ("other", "1005.3.2", "0.2", "0.15"),
    ):
        load_key, width_key = f"{key}_occupant_load", f"{key}_clear_width_in"
        load = _number(measurements.get(load_key))
        if load is not None and load != load.to_integral_value():
            load = None
        actual = _number(measurements.get(width_key))
        factor = Decimal(exception if reduced else normal)
        threshold = load * factor if load is not None and applicable else None
        emit("IBC", "exit_capacity", f"IBC-2024-{section}-capacity", section,
             threshold, actual, "in",
             f"component-specific occupant load × {factor} in/person; separate width minima not checked",
             [load_key, width_key, "egress_factor_basis", "other_egress_exceptions_excluded"],
             applicable and load is not None)

    # NFPA 101-2024, Chapter 7. Emergency illumination requirements are
    # conditional on the occupancy and applicable code sections. These checks
    # intentionally cover only duration and floor-level photometry.
    lighting = measurements.get("emergency_lighting_required_confirmed") is True
    for field, section, threshold, unit, direction in (
        ("emergency_duration_minutes", "7.9.2.1", "90", "min", "min"),
        ("initial_average_fc", "7.9.2.1.1", "1.0", "fc", "min"),
        ("initial_minimum_fc", "7.9.2.1.1", "0.1", "fc", "min"),
        ("final_average_fc", "7.9.2.1.2", "0.6", "fc", "min"),
        ("final_minimum_fc", "7.9.2.1.2", "0.06", "fc", "min"),
    ):
        actual = _number(measurements.get(field), zero_allowed=True)
        eligible = lighting and (field == "emergency_duration_minutes" or
                                 measurements.get("floor_level_egress_photometry_confirmed") is True)
        emit("NFPA 101", "emergency_lighting", f"NFPA101-2024-{section}-{field}",
             section, Decimal(threshold), actual, unit, f"declared {field} >= {threshold}",
             [field, "emergency_lighting_required_confirmed",
              "floor_level_egress_photometry_confirmed"], eligible, direction)
    peak = _number(measurements.get("measured_maximum_fc"), zero_allowed=True)
    low = _number(measurements.get("measured_minimum_fc"))
    ratio = peak / low if peak is not None and low and peak >= low else None
    emit("NFPA 101", "emergency_lighting", "NFPA101-2024-7.9.2.1.3-uniformity",
         "7.9.2.1.3", Decimal("40"), ratio, "ratio", "maximum / minimum <= 40",
         ["measured_maximum_fc", "measured_minimum_fc", "floor_level_egress_photometry_confirmed"],
         lighting and measurements.get("floor_level_egress_photometry_confirmed") is True,
         "max")

    # A category without a verified rule is NOT a passing check. Expose every
    # requested gap for the qualified reviewer, including other rules in the
    # supported categories (only a subset of those provisions was evaluated).
    coverage = []
    for family, categories in COVERAGE.items():
        for category in categories:
            supported = [f["rule_id"] for f in findings
                         if f["code_family"] == family and f["category"] == category]
            coverage.append({
                "code_family": family, "category": category,
                "coverage": "partial_numeric_rules" if supported else "not_implemented",
                "rule_ids": supported, "full_category_compliance": "unknown",
            })
    counts = {status: sum(f["result"] == status for f in findings)
              for status in ("pass", "fail", "unknown")}
    missing = sorted(set(
        field for f in findings if f["result"] == "unknown"
        for field in f["required_inputs"]
        if measurements.get(field) is None
    ))
    if not context_ready:
        missing.append("jurisdiction, adoption/amendments, reviewer, building facts and project source evidence")
    for family in enabled:
        if not enabled[family]:
            missing.append(f"{family} 2024 applicability and edition not confirmed")
    return {
        "assessment_kind": "ibc_nfpa_measurements_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "overall_status": "pending_qualified_review",
        "complete_code_compliance_determined": False,
        "rule_results": findings, "counts": counts,
        "missing_information": sorted(set(missing)),
        "coverage": coverage,
        "disclaimer": "Selected 2024 IBC capacity and NFPA 101 emergency-lighting measurements only. No automatic jurisdiction determination, full rule coverage, authority approval or field verification. A pass applies only to its isolated numerical comparison. All unimplemented categories require qualified review.",
    }
