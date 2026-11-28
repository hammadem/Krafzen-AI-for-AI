import json
from app.services.aec_intent_model import MODEL,predict_intent,load_model

def test_trained_model_matches_holdout():
    model=load_model()
    rows=[json.loads(line) for line in (MODEL.parent/"aec_intent_dataset.jsonl").read_text().splitlines()]
    train=[r for r in rows if r["split"]=="train"]
    test=[r for r in rows if r["split"]=="test"]
    assert len(train)==model["training_count"]==512
    assert len(test)==model["evaluation_count"]==32
    assert len({r["text"] for r in rows})==len(rows)
    correct=sum(predict_intent(r["text"])["label"]==r["label"] for r in test)
    assert correct==model["evaluation_correct"]==31

def test_abstain_and_never_execute():
    for text in ("hello","banana recipe","IFC","IFC IFC IFC"):
        result=predict_intent(text)
        assert result["label"]=="unknown"
        assert result["advisory_only"] is True
