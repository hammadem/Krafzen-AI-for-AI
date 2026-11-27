"""Authenticated, read-only evidence catalog; never loads experimental models."""
import json
import shutil
from pathlib import Path

from app.services.aec_intent_model import load_model
from app.services.reference_retrieval import reference_register

ROOT=Path(__file__).resolve().parents[1]/"data"

def _read(name):
    with (ROOT/name).open(encoding="utf-8") as stream:
        return json.load(stream)

def model_registry():
    intent=load_model()
    symbol=_read("cad_symbol_evaluation.json")
    llm=_read("aec_llm_experiment_evidence.json")
    dataset=_read("aec_dataset_register.json")
    reference=reference_register()
    return {
        "reference_count":reference["dataset_count"],
        "references":reference["datasets"],
        "datasets":dataset["sources"],
        "models":[
            {"name":"AEC intent classifier","mode":"server_advisory","runtime_available":True,
             "training_count":intent["training_count"],"evaluation_count":intent["evaluation_count"],
             "correct":intent["evaluation_correct"],"scope":"Synthetic phrase holdout; task suggestion only.",
             "workspace_path":"/workspace"},
            {"name":"CAD symbol classifier","mode":"browser_advisory","runtime_available":True,
             "training_count":symbol["training_count"],"evaluation_count":symbol["test_count"],
             "correct":symbol["correct"],"scope":symbol["scope"],"workspace_path":"/workspace/reviews"},
            {"name":"Tesseract English OCR","mode":"pretrained_local_engine","runtime_available":bool(shutil.which("tesseract")),
             "scope":"Pretrained OCR; local executable detection only. Actual image import requires malware scanner. Text is not a verified measurement.",
             "workspace_path":"/workspace/imports"},
            {"name":"Experimental AEC language model","mode":"offline_experiment","runtime_available":False,
             "training_count":llm["training_rows"],"evaluation_count":llm["evaluation_rows"],
             "correct":llm["after_correct"],"baseline_correct":llm["before_correct"],"scope":llm["scope"],
             "workflow_run":llm["workflow_run"],"artifact":llm["artifact"],
             "artifact_retention_days":llm["artifact_retention_days"],"source_sha256":llm["source_sha256"]},
        ],
        "scope":"Evidence of bounded training and reference processing, not professional verification. No customer data enters the public corpus."
    }
