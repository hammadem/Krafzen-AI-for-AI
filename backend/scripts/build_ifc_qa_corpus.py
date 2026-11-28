"""Generate factual BIM QA from approved IFC source; never from customer files."""
from hashlib import sha256
from pathlib import Path
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.reference_retrieval import _index

# Keep the Simple-Scene family together across schema versions and disciplines.
# Hold out isolated column and basin examples. This is source-group isolation,
# not proof that the upstream models have no common geometric components.
def group(row):
    name=row["dataset_id"]
    if any(x in name for x in ("architecture","structural","hvac","electrical")):return "simple_scene"
    if "basin" in name:return "basin"
    if "column" in name:return "column"
    return name.removesuffix(".ifc")

def generate():
    rows=[];seen=set()
    for doc in _index():
        source_group=group(doc)
        split="test" if source_group in ("column","basin") else "train"
        facts=[("What IFC schema does this reference model declare?",doc["schema"])]
        for entity,count in sorted(doc["entity_counts"].items()):
            facts.append((f"How many {entity} product instances are in this reference model?",str(count)))
        facts.append(("Which product classes occur in this reference model?",", ".join(sorted(doc["entity_counts"]))))
        for question,answer in facts:
            key=(doc["sha256"],question)
            if key in seen:continue
            seen.add(key)
            rows.append({"question":question,"answer":answer,"dataset_id":doc["dataset_id"],"source_group":source_group,
                         "split":split,"source_sha256":doc["sha256"],"source_url":doc["source_url"],
                         "license":doc["license"],"attribution":doc["attribution"],
                         "scope":"Exact product classes and counts parsed from reference IFC; not a real building or code approval."})
    if not rows or {r["source_group"] for r in rows if r["split"]=="train"} & {r["source_group"] for r in rows if r["split"]=="test"}:raise ValueError("Invalid source split")
    return rows

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);args=p.parse_args()
    rows=generate();args.output_dir.mkdir(parents=True,exist_ok=True)
    data="".join(json.dumps(r,sort_keys=True)+"\n" for r in rows)
    (args.output_dir/"ifc_source_qa.jsonl").write_text(data,encoding="utf-8")
    report={"rows":len(rows),"train":sum(r["split"]=="train" for r in rows),"test":sum(r["split"]=="test" for r in rows),
            "source_models":len({r["source_sha256"] for r in rows}),"sha256":sha256(data.encode()).hexdigest(),
            "scope":"Parser-derived factual QA corpus, not trained LLM weights."}
    (args.output_dir/"ifc_source_qa_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report))
