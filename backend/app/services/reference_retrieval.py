"""Local license-gated index of original buildingSMART IFC certification fixtures."""
from collections import Counter
from functools import lru_cache
from hashlib import sha1, sha256
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2] / "tests/fixtures/aec_reference"
LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"
STOP = {"what","how","where","which","the","a","an","are","is","do","does","in","of","for","to","and","me","show","tell","reference","many","can","i","example"}
GENERIC = {"ifc", "model", "file", "source", "project", "customer", "sample", "certification", "count", "data", "evidence", "construction", "verified", "describe", "result"}

def tokens(value):
    words = {w for w in re.findall(r"[a-z0-9]+", value.casefold()) if w not in STOP and len(w)>1}
    return {w[:-1] if w.endswith("s") and not w.endswith(("ss", "us", "is")) and len(w)>3 else w for w in words}

def _load_index(root):
    import ifcopenshell
    root=Path(root).resolve()
    manifest=json.loads((root/"reference_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("license")!=LICENSE or not (root/"BUILDINGSMART_LICENSE.txt").is_file():
        raise ValueError("Reference license not approved")
    items=manifest["ifc_files"]
    if not 1<=len(items)<=30: raise ValueError("Reference dataset budget exceeded")
    docs=[]
    seen=set()
    for item in items:
        path=(root/item["name"]).resolve()
        if path.parent!=root or path.suffix.lower()!=".ifc" or path.stat().st_size>4*1024*1024:
            raise ValueError("Unsafe reference source")
        raw=path.read_bytes()
        git_hash=sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()
        if git_hash!=item["blob"]: raise ValueError("Reference source integrity mismatch")
        digest=sha256(raw).hexdigest()
        if digest in seen: continue
        seen.add(digest)
        if not item["source_url"].startswith("https://github.com/buildingSMART/Certification-datasets/blob/main/"):
            raise ValueError("Reference source not approved")
        model=ifcopenshell.open(str(path))
        if str(model.schema_identifier) != item["schema"]:
            raise ValueError("Reference schema mismatch")
        counts=Counter(str(e.is_a()) for e in model.by_type("IfcProduct"))
        if len(counts)>200: raise ValueError("Reference class budget exceeded")
        for entity,min_count in item.get("expected_min",{}).items():
            if len(model.by_type(entity))<min_count: raise ValueError("Reference entity checks failed")
        classification=item["classification"]
        discipline="structural" if "structural" in classification.lower() else "mep" if "mep" in classification.lower() else "architecture"
        classes=dict(sorted(counts.items()))
        content=(f"Certification sample: {classification}. IFC schema {model.schema_identifier}. "
                 +"Source product classes: "+", ".join(f"{key}: {count}" for key,count in classes.items())+". "
                 +"Counts describe this reference model only, not a customer's project or verified construction.")
        terms=" ".join(re.sub(r"([a-z])([A-Z])",r"\1 \2",k).lower() for k in classes)
        docs.append({"dataset_id":item["name"],"title":classification,"discipline":discipline,
                     "schema":str(model.schema_identifier),"format":"IFC","version":item["blob"],
                     "sha256":digest,"source_url":item["source_url"],"license":LICENSE,
                     "license_url":manifest["license_url"],"attribution":manifest["attribution"],
                     "commercial_use":"CC BY 4.0 permits commercial reuse with attribution",
                     "processing_status":"parsed_hash_verified","entity_counts":classes,
                     "content":content,"search_text":f"{item['name']} {classification} {discipline} {model.schema} {terms}"})
    return docs

@lru_cache(maxsize=1)
def _index():
    return _load_index(ROOT)

def reference_register():
    rows=_index()
    return {"dataset_count":len(rows),"retrieval_method":"local_lexical_reference_v1",
            "datasets":[{k:v for k,v in row.items() if k not in {"search_text","content","entity_counts"}} for row in rows],
            "scope":"Reference IFC certification fixtures only. Separate intent model is trained on original synthetic text, not these files. No customer data or codebook ingestion."}

def retrieve_reference(question):
    # Generic query words and boilerplate caveats are not technical evidence.
    # A specific unsupported question must not retrieve a random IFC example
    # merely because it contains the word IFC, model, or project.
    words=tokens(question) - GENERIC
    if not words: return []
    docs=_index()
    terms=[tokens(row["search_text"]) - GENERIC for row in docs]
    scored=[]
    for row,term_set in zip(docs,terms):
        common=words&term_set
        if not common: continue
        score=sum(math.log(1+(len(docs)+1)/(1+sum(w in t for t in terms))) for w in common)
        score+=2*len(words&tokens(row["title"]))
        scored.append((score,len(common),row))
    scored.sort(key=lambda v:(-v[0],-v[1],v[2]["dataset_id"]))
    return [{k:v for k,v in row.items() if k!="search_text"} for _,_,row in scored[:3]]

def format_reference_answer(hits):
    if not hits:
        return "No matching approved reference was found. This library currently covers licensed buildingSMART IFC certification examples only. No engineering finding can be inferred from the missing reference."
    parts=["Retrieved reference evidence (not a design or code-compliance decision):"]
    for i,row in enumerate(hits,1):
        parts.extend([f"{i}. {row['title']} — {row['schema']}",row["content"],
                      f"Source: {row['source_url']}",f"License: {row['license']}; {row['attribution']}",
                      f"Source SHA-256: {row['sha256']}"])
    parts.append("Use the actual project drawing or model for customer-specific quantities, geometry and code checks. These reference examples do not certify those results.")
    return "\n\n".join(parts)
