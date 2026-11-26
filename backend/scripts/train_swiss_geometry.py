"""Offline-only Swiss Dwellings geometry experiment, no customer data.
Only geometry class/shape features are retained; no location records, raw IDs,
coordinates, full layouts or source image assets enter the output.
"""
import argparse,csv,hashlib,io,json,math,random,zipfile
from pathlib import Path

SOURCE="https://zenodo.org/records/7788422"
MD5="3b7915ecd5bf8e492a3e78c598b74123"
ATTRIBUTION="Standfest et al., Archilyse AG, Swiss Dwellings v3.0.0 (2022), DOI 10.5281/zenodo.7788422, CC BY 4.0."
CLASSES={"WALL","DOOR","WINDOW","COLUMN","LIVING_ROOM","BEDROOM","KITCHEN","BATHROOM"}

def digest(path):
    h=hashlib.md5();s=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block);s.update(block)
    if h.hexdigest()!=MD5:raise ValueError("Published archive checksum mismatch")
    return s.hexdigest()

def collect(path):
    from shapely import wkt
    source_hash=digest(path)
    groups={};seen=set();counts={};invalid=0
    with zipfile.ZipFile(path) as archive:
        members=[m for m in archive.infolist() if Path(m.filename).name=="geometries.csv" and not m.is_dir()]
        if len(members)!=1 or not 0<members[0].file_size<=3_000_000_000:raise ValueError("Unexpected geometry archive")
        with archive.open(members[0]) as raw:
            reader=csv.DictReader(io.TextIOWrapper(raw,encoding="utf-8-sig",newline=""))
            if not {"building_id","entity_subtype","geometry"}<=set(reader.fieldnames or []):raise ValueError("Unexpected source schema")
            for i,row in enumerate(reader):
                if i>=400000:break
                label=row["entity_subtype"].strip().upper()
                building=row["building_id"].strip()
                if label not in CLASSES or not building or len(row["geometry"])>100000:continue
                # Stable building-level split, never retain actual IDs.
                group=hashlib.sha256(("swiss-v3-building:"+building).encode()).hexdigest()
                split="test" if int(group[:8],16)%5==0 else "train"
                key=(split,label)
                if counts.get(key,0)>=1500:continue
                try:
                    geom=wkt.loads(row["geometry"])
                    if geom.geom_type not in ("Polygon","MultiPolygon") or geom.is_empty or not geom.is_valid:continue
                    x0,y0,x1,y1=geom.bounds;w=x1-x0;h=y1-y0;area=geom.area;perimeter=geom.length
                    if not all(math.isfinite(v) for v in (w,h,area,perimeter)) or min(w,h,area,perimeter)<=0 or max(w,h)>1000:continue
                    # Translation/rotation-invariant coarse features, no locations.
                    rect=geom.minimum_rotated_rectangle
                    coords=list(rect.exterior.coords)
                    sides=sorted(math.dist(coords[j][:2],coords[j+1][:2]) for j in range(4))
                    a,b=sides[0],sides[-1]
                    if a<=0 or b<=0:continue
                    features=[round(area,4),round(perimeter,4),round(a,4),round(b,4),round(a/b,4),
                        round(area/(a*b),4),round(4*math.pi*area/(perimeter*perimeter),4)]
                    # Remove identical normalized shape-feature duplicates across splits.
                    identity=hashlib.sha256(json.dumps(features).encode()).hexdigest()
                    if identity in seen:continue
                    seen.add(identity);counts[key]=counts.get(key,0)+1
                    groups.setdefault(group,[]).append({"split":split,"label":label,"features":features,"group":group})
                except Exception:
                    invalid+=1
    rows=[r for group in groups.values() for r in group]
    return rows,source_hash,invalid

def train(rows):
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report,confusion_matrix
    train=[r for r in rows if r["split"]=="train"];test=[r for r in rows if r["split"]=="test"]
    if len(train)<100 or len(test)<30 or len({r["group"] for r in train})<3 or len({r["group"] for r in test})<2:raise ValueError("Insufficient building-disjoint evidence")
    if {r["group"] for r in train}&{r["group"] for r in test}:raise ValueError("Building leakage")
    model=RandomForestClassifier(n_estimators=64,max_depth=12,min_samples_leaf=4,random_state=44,n_jobs=2,class_weight="balanced")
    model.fit([r["features"] for r in train],[r["label"] for r in train])
    predicted=model.predict([r["features"] for r in test])
    labels=sorted(set(r["label"] for r in rows))
    y=[r["label"] for r in test]
    # Safe nonexecutable model serialization; no pickle.
    trees=[]
    for estimator in model.estimators_:
        t=estimator.tree_
        trees.append({"left":t.children_left.tolist(),"right":t.children_right.tolist(),"feature":t.feature.tolist(),
            "threshold":t.threshold.tolist(),"values":t.value[:,0,:].tolist()})
    artifact={"format":"swiss_geometry_rf_v1","classes":model.classes_.tolist(),"trees":trees,
        "features":["area_m2","perimeter_m","min_rotated_width_m","max_rotated_width_m","aspect_ratio","rectangularity","compactness"]}
    report={"train_rows":len(train),"test_rows":len(test),"train_buildings":len({r["group"] for r in train}),
        "test_buildings":len({r["group"] for r in test}),"accuracy":float(np.mean(predicted==y)),
        "classification_report":classification_report(y,predicted,labels=labels,output_dict=True,zero_division=0),
        "confusion_matrix":confusion_matrix(y,predicted,labels=labels).tolist(),"labels":labels,
        "scope":"Real public vector polygon feature classification. Not symbol detection, pixel segmentation, building-code or drawing approval. No raw layout or location released."}
    return artifact,report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args()
    rows,source_hash,invalid=collect(a.archive);model,report=train(rows)
    report.update(source_url=SOURCE,source_archive_sha256=source_hash,attribution=ATTRIBUTION,license="CC BY 4.0",invalid_rows=invalid)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    # Group IDs are only internal split keys. Drop them from stored data.
    (a.output_dir/"geometry_features.jsonl").write_text("".join(json.dumps({k:v for k,v in r.items() if k!="group"})+"\n" for r in rows))
    (a.output_dir/"geometry_model.json").write_text(json.dumps(model)+"\n")
    (a.output_dir/"geometry_evaluation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("classification_report","confusion_matrix")}))
