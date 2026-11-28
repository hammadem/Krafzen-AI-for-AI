"""CPU-only, bounded AEC context extraction experiment. Not a production model.

Only approved IFC fixtures are used. Never train on customer drawings or
copyrighted codebooks. This script does not modify the application model.
"""
from pathlib import Path
import argparse, hashlib, json, random, re, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.reference_retrieval import _index
from scripts.build_ifc_qa_corpus import generate

BASE="HuggingFaceTB/SmolLM2-135M-Instruct"
REVISION="ee72e5415c002e8fc0566a191a07c0b2b708875a"

def examples():
    docs={d["dataset_id"]:d for d in _index()}
    rows=generate()
    output=[]
    for row in rows:
        doc=docs[row["dataset_id"]]
        evidence={"schema":doc["schema"],"product_counts":doc["entity_counts"]}
        prompt="Read the supplied reference-model evidence. Return only the exact answer. Do not infer unknown values.\nEvidence: "+json.dumps(evidence,sort_keys=True)+"\nQuestion: "+row["question"]
        output.append({**row,"prompt":prompt})
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--steps",type=int,default=24)
    args=p.parse_args()
    if not 1<=args.steps<=64:raise ValueError("CPU experiment step limit is 64")
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer
    from peft import LoraConfig,get_peft_model
    torch.set_num_threads(2);torch.manual_seed(44);random.seed(44)
    rows=examples()
    training=[r for r in rows if r["split"]=="train"]
    evaluation=[r for r in rows if r["split"]=="test"]
    if not training or not evaluation:raise ValueError("Missing source-disjoint data")
    if {r["source_group"] for r in training}&{r["source_group"] for r in evaluation}:raise ValueError("Source overlap")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    tokenizer=AutoTokenizer.from_pretrained(BASE,revision=REVISION,trust_remote_code=False)
    model=AutoModelForCausalLM.from_pretrained(BASE,revision=REVISION,trust_remote_code=False,
        use_safetensors=True,torch_dtype=torch.float32)
    def prompt_text(row):
        return tokenizer.apply_chat_template([{"role":"user","content":row["prompt"]}],tokenize=False,add_generation_prompt=True)
    def evaluate(net):
        net.eval();results=[]
        for row in evaluation[:12]:
            inputs=tokenizer(prompt_text(row),return_tensors="pt",truncation=True,max_length=768)
            with torch.no_grad():
                generated=net.generate(**inputs,max_new_tokens=48,do_sample=False,pad_token_id=tokenizer.eos_token_id)
            predicted=tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:],skip_special_tokens=True).strip()
            norm=lambda x:" ".join(x.casefold().strip().split())
            results.append({"dataset_id":row["dataset_id"],"question":row["question"],"expected":row["answer"],
                            "prediction":predicted,"exact_match":norm(predicted)==norm(row["answer"])})
        return {"count":len(results),"correct":sum(x["exact_match"] for x in results),"results":results}
    before=evaluate(model)
    model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,target_modules=["q_proj","v_proj"],lora_dropout=0.05,task_type="CAUSAL_LM"))
    optimizer=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=3e-4)
    model.train();losses=[]
    shuffled=training[:];random.shuffle(shuffled)
    for step in range(args.steps):
        row=shuffled[step%len(shuffled)]
        prompt=prompt_text(row)
        prefix=tokenizer(prompt,add_special_tokens=False).input_ids
        target=tokenizer(row["answer"]+tokenizer.eos_token,add_special_tokens=False).input_ids
        if len(prefix)+len(target)>768:continue
        input_ids=torch.tensor([prefix+target],dtype=torch.long)
        labels=torch.tensor([[-100]*len(prefix)+target],dtype=torch.long)
        optimizer.zero_grad()
        loss=model(input_ids=input_ids,attention_mask=torch.ones_like(input_ids),labels=labels).loss
        if not torch.isfinite(loss):raise ValueError("Nonfinite training loss")
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
        losses.append(float(loss.detach()))
        print(f"step {step+1} loss {losses[-1]:.5f}",flush=True)
    if not losses:raise ValueError("No training steps completed")
    after=evaluate(model)
    model.save_pretrained(args.output_dir/"adapter",safe_serialization=True)
    tokenizer.save_pretrained(args.output_dir/"tokenizer")
    corpus="\n".join(json.dumps(r,sort_keys=True) for r in rows)
    report={"base_model":BASE,"revision":REVISION,"license":"Apache-2.0 base; CC BY 4.0 IFC corpus attribution retained",
            "train_rows":len(training),"heldout_rows":len(evaluation),"steps":len(losses),"losses":losses,
            "source_sha256":hashlib.sha256(corpus.encode()).hexdigest(),"before":before,"after":after,
            "scope":"Source-group-separated reference extraction experiment, not independent real-world design evaluation.",
            "production_approved":False}
    (args.output_dir/"evaluation.json").write_text(json.dumps(report,indent=2)+"\n")
    (args.output_dir/"source_manifest.jsonl").write_text(corpus+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("before","after","losses")}))
    print(f"Exact match before {before['correct']}/{before['count']}; after {after['correct']}/{after['count']}")
if __name__=="__main__":main()
