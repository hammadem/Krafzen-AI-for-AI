"use client";
import {useEffect,useState} from "react";
import {getMultidisciplineCatalog,saveMultidisciplineAssessment} from "@/lib/api/api";
type User=Parameters<typeof saveMultidisciplineAssessment>[0];
type Rule={rule_id:string;code_family:string;edition:string;section_reference:string;title:string;unit:string;applicability:string;extra_input:string|null;source_url:string};
type Entry={rule_id:string;adopted_edition:string;element_reference:string;applicability_confirmed:boolean;measured:number|null;extra_value:number|null};
export default function MultidisciplinePanel({user,projectId,sourceFile,context,onSaved}:{user:User;projectId:string;sourceFile:string;context:{state:string;municipality:string;project_address:string;occupancy:string;building_type:string};onSaved:(record:unknown)=>void}){
 const [rules,setRules]=useState<Rule[]>([]),[id,setId]=useState(""),[entries,setEntries]=useState<Entry[]>([]);
 const [edition,setEdition]=useState(""),[element,setElement]=useState(""),[measured,setMeasured]=useState(""),[extra,setExtra]=useState(""),[applies,setApplies]=useState(false);
 const [adoption,setAdoption]=useState(""),[reviewer,setReviewer]=useState(""),[credential,setCredential]=useState(""),[amendments,setAmendments]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
 useEffect(()=>{let active=true;if(!user?.access_token)return;void getMultidisciplineCatalog(user).then(r=>{if(!active)return;const data=r.data as unknown as {rules?:Rule[]};if(r.ok&&Array.isArray(data?.rules))setRules(data.rules);else setError(r.error?.message||"Rule catalog unavailable");}).catch(()=>{if(active)setError("Rule catalog unavailable");});return()=>{active=false};},[user]);
 const rule=rules.find(r=>r.rule_id===id);
 const reset=()=>{setEdition("");setElement("");setMeasured("");setExtra("");setApplies(false);};
 function add(){
   if(!rule||entries.length>=50)return;
   const n=(s:string)=>s.trim()===""?null:Number(s);
   const a=n(measured),b=n(extra);
   if([a,b].some(v=>v!==null&&(!Number.isFinite(v)||v<0||v>1e9))){setError("Invalid measurement");return;}
   if(entries.some(e=>e.rule_id===id&&e.element_reference.trim().toLowerCase()===element.trim().toLowerCase())){setError("Duplicate rule and element");return;}
   setEntries(old=>[...old,{rule_id:id,adopted_edition:edition,element_reference:element,applicability_confirmed:applies,measured:a,extra_value:rule.extra_input?b:null}]);reset();setError("");
 }
 async function save(){
   if(!projectId||!entries.length||busy)return;
   setBusy(true);setError("");
   try{const r=await saveMultidisciplineAssessment(user,{project_id:projectId,source_file_id:sourceFile||null,jurisdiction:{...context,adoption_reference:adoption,reviewer_name:reviewer,reviewer_credential:credential,local_amendments_reviewed_no_conflict:amendments},entries});
   if(!r.ok)throw Error(r.error?.message||"Assessment could not be saved");onSaved(r.data);setEntries([]);}
   catch(e){setError(e instanceof Error?e.message:"Assessment failed");}finally{setBusy(false);}
 }
 const style="block w-full rounded-lg border border-white/20 bg-slate-900 p-2";
 return <section className="space-y-4 rounded-xl border border-white/10 p-5">
 <h2 className="font-semibold">Multidiscipline code measurement catalog</h2>
 <p className="text-sm text-amber-200">Selected ADA, IBC, NFPA 10, IRC, NEC, IPC, IMC, IECC and ASCE 7 checks. Results are isolated comparisons, not verified engineering approval. Use the adopted edition, actual source evidence and a qualified reviewer. Unknown values remain unknown.</p>
 <div className="grid gap-3 sm:grid-cols-2">
 <label>Adoption / ordinance reference<input className={style} value={adoption} onChange={e=>setAdoption(e.target.value)}/></label>
 <label>Reviewer name<input className={style} value={reviewer} onChange={e=>setReviewer(e.target.value)}/></label>
 <label>Reviewer credential / jurisdiction (asserted)<input className={style} value={credential} onChange={e=>setCredential(e.target.value)}/></label>
 </div><label className="flex gap-2 text-sm"><input type="checkbox" checked={amendments} onChange={e=>setAmendments(e.target.checked)}/>Reviewer checked adoption and local amendments; no conflict with selected rules.</label>
 <label>Rule<select className={style} value={id} onChange={e=>{setId(e.target.value);reset();}}><option value="">Select a rule</option>{rules.map(r=><option key={r.rule_id} value={r.rule_id}>{r.code_family} {r.edition} §{r.section_reference} — {r.title}</option>)}</select></label>
 {rule&&<div className="space-y-3"><p className="text-sm">{rule.applicability} <a href={rule.source_url} target="_blank" rel="noreferrer" className="underline">Source</a></p>
 <div className="grid gap-3 sm:grid-cols-2">
 <label>Adopted edition<select className={style} value={edition} onChange={e=>setEdition(e.target.value)}><option value="">Unknown / other edition</option><option value={rule.edition}>{rule.edition}</option></select></label>
 <label>Element / drawing reference<input className={style} value={element} onChange={e=>setElement(e.target.value)}/></label>
 <label>{rule.code_family==="ASCE 7"?"Declared design resistance":"Measured value"} ({rule.unit})<input className={style} type="number" min="0" step="any" value={measured} onChange={e=>setMeasured(e.target.value)}/></label>
 {rule.extra_input&&<label>{rule.extra_input}<input className={style} type="number" min="0" step="any" value={extra} onChange={e=>setExtra(e.target.value)}/></label>}
 </div><label className="flex gap-2 text-sm"><input type="checkbox" checked={applies} onChange={e=>setApplies(e.target.checked)}/>Qualified reviewer confirms the stated scope and exclusions.</label>
 <button type="button" onClick={add} disabled={busy||entries.length>=50} className="rounded border border-white/20 p-2">Add measurement to assessment</button></div>}
 {entries.map((e,i)=><div className="flex justify-between gap-2 text-sm" key={i}><span>{e.rule_id} · {e.element_reference||"Unspecified element"} · {e.measured??"Unknown"}</span><button type="button" disabled={busy} onClick={()=>setEntries(old=>old.filter((_,j)=>j!==i))} className="underline">Remove</button></div>)}
 {error&&<p role="alert" className="text-red-300">{error}</p>}
 <button type="button" onClick={()=>void save()} disabled={busy||!projectId||!entries.length} className="rounded-lg bg-sky-300 px-4 py-2 text-slate-950 disabled:opacity-40">{busy?"Saving…":"Evaluate and save multidisciplinary evidence"}</button>
 </section>;
}
