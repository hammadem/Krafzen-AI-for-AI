"""Advisory-only AEC intent classifier, no external provider calls or automatic execution."""
from functools import lru_cache
from pathlib import Path
import json
import math
import re

MODEL=Path(__file__).resolve().parents[1]/"data"/"aec_intent_model.json"

@lru_cache(maxsize=1)
def load_model():
    with MODEL.open(encoding="utf-8") as stream:
        model=json.load(stream)
    if model.get("format")!="aec_multinomial_nb_v1" or not 1<=len(model["labels"])<=12 or not 1<=len(model["vocab"])<=5000:
        raise ValueError("Unsupported AEC model")
    return model

def predict_intent(text):
    model=load_model()
    vocab=set(model["vocab"])
    words=re.findall(r"[a-z0-9]+",text[:2000].lower())
    known=[w for w in words if w in vocab]
    if len(set(known))<2 or len(known)/max(len(words),1)<0.35:
        return {"label":"unknown","confidence":0.0,"advisory_only":True}
    scores=sorted(((label,model["priors"][label]+sum(model["weights"][label][w] for w in known)) for label in model["labels"]),key=lambda x:(-x[1],x[0]))
    probability=1/sum(math.exp(s-scores[0][1]) for _,s in scores)
    label=scores[0][0] if probability>=model["minimum_confidence"] else "unknown"
    return {"label":label,"confidence":round(probability,6),"advisory_only":True,
            "model_version":model["format"],"scope":"Intent suggestion only; never executes tools, interprets geometry or determines compliance."}
