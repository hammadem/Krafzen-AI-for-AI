import pytest
from app.services.multidiscipline_rules import RULES,evaluate_multidiscipline
CTX={"state":"QA","municipality":"Test","project_address":"100 Test Road","occupancy":"B","building_type":"office","adoption_reference":"test ordinance","reviewer_name":"test reviewer","reviewer_credential":"test fixture","local_amendments_reviewed_no_conflict":True}
def check(rule,value,extra=None,**changes):
    entry={"rule_id":rule["rule_id"],"adopted_edition":rule["edition"],"element_reference":"Sheet A1 / test", "applicability_confirmed":True,"measured":value,"extra_value":extra,**changes}
    return evaluate_multidiscipline(context=CTX,entries=[entry],source_file_id="file",source_version=2)

@pytest.mark.parametrize("rule",RULES,ids=lambda r:r["rule_id"])
def test_all_catalog_boundaries(rule):
    extra=40 if rule["code_family"]=="NEC" else 100 if rule["code_family"]=="ASCE 7" else None
    threshold=40 if rule["code_family"]=="NEC" else 140 if rule["code_family"]=="ASCE 7" else rule["threshold"]
    assert check(rule,threshold,extra)["counts"]["pass"]==1
    bad=threshold-0.01 if rule["direction"]=="min" else threshold+0.01
    report=check(rule,bad,extra)
    assert report["counts"]["fail"]==1
    assert report["complete_code_compliance_determined"] is False
    assert report["rule_results"][0]["evidence"]["source_file_version"]==2
    assert check(rule,threshold,extra,adopted_edition="other")["counts"]["unknown"]==1
    assert check(rule,threshold,extra,applicability_confirmed=False)["counts"]["unknown"]==1

def test_pdf_integration_and_missing_evidence():
    from app.services.compliance_pdf_service import build_compliance_pdf
    rule=RULES[0]
    report=check(rule,30)
    assert build_compliance_pdf({"id":"assessment","project_id":"project","source_file_id":"file","jurisdiction":CTX,"measurements":{},"result":report}).startswith(b"%PDF-")
    r=evaluate_multidiscipline(context=CTX,entries=[{"rule_id":rule["rule_id"],"measured":30,"adopted_edition":"2010","element_reference":"A1","applicability_confirmed":True}],source_file_id=None,source_version=None)
    assert r["counts"]["unknown"]==1
