"""Limited, source-referenced checks; not a full code or structural review."""
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite

SOURCES = {
    "ADA": "https://www.access-board.gov/ada/",
    "IBC": "https://codes.iccsafe.org/content/IBC2024V2.0/chapter-10-means-of-egress",
    "NFPA 10": "https://www.nfpa.org/news-blogs-and-articles/blogs/2021/04/30/extinguisher-placement-guide",
    "IRC": "https://codes.iccsafe.org/content/IRC2021P1/chapter-3-building-planning",
    "NEC": "https://www.nfpa.org/news-blogs-and-articles/blogs/2022/12/21/electrical-room-basics-part-2",
    "IPC": "https://codes.iccsafe.org/content/IPC2024P1/chapter-4-fixtures-faucets-and-fixture-fittings",
    "IMC": "https://codes.iccsafe.org/content/IMC2021P1/chapter-3-general-regulations",
    "IECC": "https://codes.iccsafe.org/content/IECC2015/chapter-4-re-residential-energy-efficiency",
    "ASCE 7": "https://www.asce.org/publications-and-news/codes-and-standards/asce-sei-7-22/",
}
# Each entry is a narrowly scoped numerical comparison. The reviewer must
# identify the exact element, verify the edition and exclude exceptions.
def rule(id, family, edition, section, title, category, unit, direction, threshold, applicability, extra=None):
    return {"rule_id":id,"code_family":family,"edition":edition,"section_reference":section,
            "title":title,"category":category,"unit":unit,"direction":direction,
            "threshold":threshold,"applicability":applicability,"source_url":SOURCES[family],
            "extra_input":extra}

RULES = [
    rule("ADA-305.3-width","ADA","2010","305.3","Clear floor space width","accessibility","in","min",30,"Required unobstructed rectangular clear floor space; approach/orientation, alcove and additional requirements verified separately."),
    rule("ADA-305.3-length","ADA","2010","305.3","Clear floor space length","accessibility","in","min",48,"Required unobstructed rectangular clear floor space; approach/orientation and alcove requirements verified separately."),
    rule("ADA-308.2.1-low","ADA","2010","308.2.1","Lowest unobstructed adult forward reach","accessibility","in","min",15,"Adult forward reach, unobstructed; no special exception or alternative reach condition."),
    rule("ADA-308.2.1-high","ADA","2010","308.2.1","Highest unobstructed adult forward reach","accessibility","in","max",48,"Adult forward reach, unobstructed; no special exception or alternative reach condition."),
    rule("IBC-1010.1.1-width","IBC","2024","1010.1.1","Ordinary required egress door clear opening","exit_access","in","min",32,"Ordinary egress door, measured clear opening; excludes special occupancy, bed movement, exceptions and other width/capacity requirements."),
    rule("NFPA10-6.2.1.1-travel","NFPA 10","2022","Table 6.2.1.1","Maximum actual travel to Class A extinguisher","fire_extinguishers","ft","max",75,"Class A hazard; applicable rating, coverage area, floor layout and exceptions independently reviewed; measure along actual path, not straight-line radius."),
    rule("IRC-R304.1-area","IRC","2021","R304.1","Qualifying habitable room floor area","habitable_rooms","ft²","min",70,"Non-kitchen habitable room; area qualifies under ceiling-height rules; no applicable exception."),
    rule("IRC-R304.2-width","IRC","2021","R304.2","Minimum horizontal habitable-room dimension","habitable_rooms","ft","min",7,"Non-kitchen habitable room; minimum horizontal dimension, no applicable exception."),
    rule("IRC-R305.1-height","IRC","2021","R305.1","Habitable-room ceiling height","habitable_rooms","ft","min",7,"Ordinary flat-ceiling habitable room; excludes bathrooms, special rooms, beams and sloped ceiling exceptions."),
    rule("NEC-110.26A2-width","NEC","2023","110.26(A)(2)","Electrical equipment working-space width","electrical_clearance","in","min",30,"Covered equipment likely to require energized servicing; working space, equipment width and applicable exceptions reviewed. Depth, height and door opening are separate checks.","Equipment width (in)"),
    rule("IPC-405.3.1-side","IPC","2024","405.3.1","Fixture centerline to nearest side obstruction","fixture_clearance","in","min",15,"Ordinary covered fixture, measured centerline to side wall/partition/obstruction; excludes special accessibility and other requirements."),
    rule("IPC-405.3.1-front","IPC","2024","405.3.1","Clearance in front of covered fixture","fixture_clearance","in","min",21,"Ordinary water closet, urinal, lavatory or bidet; measure actual front clearance to obstruction; other spacing and accessibility requirements separate."),
    rule("IMC-306.1-width","IMC","2021","306.1","Level service space width at appliance controls","service_access","in","min",30,"Covered appliance; level service area in front of control side, no relevant exception; access/removal and other provisions separate."),
    rule("IMC-306.1-depth","IMC","2021","306.1","Level service space depth at appliance controls","service_access","in","min",30,"Covered appliance; level service area in front of control side, no relevant exception; access/removal and other provisions separate."),
    rule("IECC-R402.4.1.2-warm","IECC","2015","R402.4.1.2","Envelope leakage — climate zones 1–2","envelope_leakage","ACH50","max",5,"2015 residential IECC, climate zone 1 or 2 confirmed; valid blower-door test at 50 Pa and applicable amendments/exceptions checked."),
    rule("IECC-R402.4.1.2-cold","IECC","2015","R402.4.1.2","Envelope leakage — climate zones 3–8","envelope_leakage","ACH50","max",3,"2015 residential IECC, climate zone 3–8 confirmed; valid blower-door test at 50 Pa and applicable amendments/exceptions checked."),
    rule("ASCE7-2.3.1-dead","ASCE 7","7-22","2.3.1 (1)","Dead-load-only factored demand vs supplied design resistance","structural_load_effect","kN","min",None,"Structural engineer confirms same positive force effect, linear dead-load response, compatible design resistance and combination applicability; no additional load terms in this isolated combination. Not a full design or load combination envelope.","Unfactored dead-load effect (kN)"),
]
CATALOG={r["rule_id"]:r for r in RULES}
SUPPORT={
    "NEC":"https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.303",
    "NFPA 10":"https://www.nfpa.org/codes-and-standards/nfpa/10",
    "ASCE 7":"https://www.iccsafe.org/wp-content/uploads/DemystifyingLoads_24IBC_ASCE7-22_EC-85122-Part1.pdf",
}
def number(value):
    if type(value) not in (int,float) or not isfinite(value) or not 0<=value<=1e9:
        return None
    return Decimal(str(value))

def evaluate_multidiscipline(*, context, entries, source_file_id, source_version):
    findings=[]
    ready=bool(source_file_id and source_version and context.get("local_amendments_reviewed_no_conflict") is True
        and all(str(context.get(k) or "").strip() for k in ("state","municipality","project_address","occupancy","building_type","adoption_reference","reviewer_name","reviewer_credential")))
    for entry in entries:
        rule=CATALOG[entry["rule_id"]]
        measured=number(entry.get("measured"))
        extra=number(entry.get("extra_value"))
        threshold=Decimal(str(rule["threshold"])) if rule["threshold"] is not None else None
        method=f'{rule["direction"]} {threshold} {rule["unit"]}'
        if rule["code_family"]=="NEC":
            threshold=max(Decimal("30"),extra) if extra is not None and extra>0 else None
            method="max(30 in, actual equipment width)"
        if rule["code_family"]=="ASCE 7":
            threshold=Decimal("1.4")*extra if extra is not None and extra>0 else None
            method="declared design resistance >= 1.4 × declared dead-load force effect; only combination (1)"
        known=ready and entry.get("adopted_edition")==rule["edition"] and entry.get("applicability_confirmed") is True and bool(str(entry.get("element_reference") or "").strip()) and measured is not None and threshold is not None
        status="unknown"
        if known:
            status="pass" if (measured>=threshold if rule["direction"]=="min" else measured<=threshold) else "fail"
        findings.append({**rule,"threshold":float(threshold) if threshold is not None else None,
            "measured":float(measured) if measured is not None else None,"result":status,
            "severity":"review_required" if status!="pass" else "informational",
            "calculation_method":method,"required_inputs":["adopted_edition","applicability_confirmed","element_reference","measured"]+(["extra_value"] if rule["extra_input"] else []),
            "jurisdiction":context,"supporting_reference_url":SUPPORT.get(rule["code_family"],rule["source_url"]),
            "evidence":{"source_file_id":source_file_id,"source_file_version":source_version,"element_reference":entry.get("element_reference"),"type":"user_declared_measurement","independently_verified":False,"reviewer_credential_verified":False},
            "explanation":("Only the isolated declared numerical condition was compared." if known else "Missing or unconfirmed edition, applicability, source, reviewer, jurisdiction or measurement."),
            "suggested_action":"Qualified reviewer must confirm adopted provisions, exceptions, measurement fidelity and remaining requirements."})
    counts={s:sum(f["result"]==s for f in findings) for s in ("pass","fail","unknown")}
    coverage=[]
    for family in SOURCES:
        subset=[f["rule_id"] for f in findings if f["code_family"]==family]
        coverage.append({"code_family":family,"category":"selected_numeric_checks","coverage":"partial_numeric_rules" if subset else "not_assessed","rule_ids":subset,"full_category_compliance":"unknown"})
    return {"assessment_kind":"multidiscipline_v1","rule_version":"multidiscipline_v1","generated_at":datetime.now(UTC).isoformat(),"overall_status":"pending_qualified_review","complete_code_compliance_determined":False,"rule_results":findings,"counts":counts,"coverage":coverage,"missing_information":["All unselected provisions and independent source/credential verification remain outstanding."], "disclaimer":"Selected edition-specific calculations only; user assertions do not establish professional licensure, adoption, authority approval or full compliance. ASCE check is one force-effect comparison, not a structural design."}
