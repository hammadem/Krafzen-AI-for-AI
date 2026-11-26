"""Fit multinomial Naive Bayes to original AEC text, no network/GPU."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse,json,math,re

ROOT=Path(__file__).resolve().parents[1]/"app"/"data"
def words(s):return re.findall(r"[a-z0-9]+",s.lower())
def fit(rows):
    if any(r["origin"]!="internally_authored_synthetic" or r["split"] not in ("train","test") for r in rows):raise ValueError("Unapproved corpus")
    train=[r for r in rows if r["split"]=="train"];test=[r for r in rows if r["split"]=="test"]
    if not train or not test or len({r["text"].strip().casefold() for r in rows})!=len(rows):raise ValueError("Duplicate or missing split")
    labels=sorted({r["label"] for r in train});vocab=sorted({w for r in train for w in words(r["text"])})
    weights={};priors={}
    for label in labels:
        subset=[r for r in train if r["label"]==label];counts=Counter(w for r in subset for w in words(r["text"]))
        total=sum(counts.values())+len(vocab)
        weights[label]={w:math.log((counts[w]+1)/total) for w in vocab}
        priors[label]=math.log(len(subset)/len(train))
    model={"format":"aec_multinomial_nb_v1","labels":labels,"vocab":vocab,"weights":weights,"priors":priors,
           "minimum_confidence":0.65,"training_count":len(train),"evaluation_count":len(test),
           "training_source":"original synthetic text; not customer data or codebook text"}
    def predict(s):
        all_words=words(s);known=[w for w in all_words if w in vocab]
        if len(set(known))<2 or len(known)/max(len(all_words),1)<0.35:return {"label":"unknown","confidence":0.0}
        scores=sorted(((l,priors[l]+sum(weights[l][w] for w in known)) for l in labels),key=lambda x:(-x[1],x[0]))
        p=1/sum(math.exp(x[1]-scores[0][1]) for x in scores)
        return {"label":scores[0][0] if p>=.65 else "unknown","confidence":p}
    results=[{**r,"prediction":predict(r["text"])} for r in test]
    correct=sum(r["label"]==r["prediction"]["label"] for r in results)
    model["evaluation_correct"]=correct
    return model,{"model":model["format"],"training_count":len(train),"evaluation_count":len(test),"correct":correct,"accuracy":correct/len(test),"results":results,
        "limitations":"Authored phrase holdout, not independent real customer validation. No foundation model fine-tuning, visual recognition or engineering approval."}

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output-dir",type=Path,required=True);args=p.parse_args()
    raw=(ROOT/"aec_intent_dataset.jsonl").read_bytes()
    model,report=fit([json.loads(line) for line in raw.splitlines()])
    report["dataset_sha256"]=sha256(raw).hexdigest()
    if report["accuracy"]<.80:raise SystemExit("Synthetic evaluation threshold not met")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"aec_intent_model.json").write_text(json.dumps(model)+"\n")
    (args.output_dir/"aec_intent_evaluation.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="results"},indent=2))
