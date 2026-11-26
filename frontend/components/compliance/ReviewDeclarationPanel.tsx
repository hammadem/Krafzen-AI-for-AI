"use client";
import {useState} from "react";
import {recordComplianceReview} from "@/lib/api/api";
type User=Parameters<typeof recordComplianceReview>[0];
type Declaration={disposition?:string;reviewer_name?:string;reviewer_credential?:string;review_reference?:string;notes?:string;recorded_at?:string};
export default function ReviewDeclarationPanel({user,id,status,declaration,onSaved}:{user:User;id:string;status:string;declaration?:Declaration;onSaved:(record:unknown)=>void}){
 const [name,setName]=useState(""),[credential,setCredential]=useState(""),[reference,setReference]=useState(""),[notes,setNotes]=useState(""),[disposition,setDisposition]=useState("reviewed"),[confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState("");
 async function submit(){
  if(!confirmed||busy)return;
  setBusy(true);setError("");
  try{const r=await recordComplianceReview(user,id,{disposition,reviewer_name:name,reviewer_credential:credential,review_reference:reference,notes,record_is_reviewer_supplied:confirmed});
   if(!r.ok)throw Error(r.error?.message||"Review declaration not saved");onSaved(r.data);
  }catch(e){setError(e instanceof Error?e.message:"Review declaration failed");}
  finally{setBusy(false);}
 }
 const cls="block w-full rounded border border-white/20 bg-slate-900 p-2";
 return <section className="space-y-3 rounded-lg border border-white/10 p-4 text-sm"><h3 className="font-semibold">Qualified reviewer declaration</h3>
 <p className="text-amber-200">Record an actual reviewer-supplied disposition, not a professional credential verification or approval for construction. The original measurements remain unchanged.</p>
 {declaration?<div className="space-y-1"><p>Recorded: {declaration.disposition} · {declaration.reviewer_name}</p><p>{declaration.reviewer_credential} · {declaration.review_reference}</p><p>{declaration.notes}</p><p>{declaration.recorded_at}</p></div>:status==="pending_qualified_review"?<>
 <label>Review disposition<select className={cls} value={disposition} onChange={e=>setDisposition(e.target.value)}><option value="reviewed">Review recorded (not approval)</option><option value="rejected">Rejected / correction required</option></select></label>
 <label>Declared reviewer name<input className={cls} value={name} onChange={e=>setName(e.target.value)}/></label>
 <label>Declared credential and jurisdiction<input className={cls} value={credential} onChange={e=>setCredential(e.target.value)}/></label>
 <label>Review reference (e.g. signed report ID)<input className={cls} value={reference} onChange={e=>setReference(e.target.value)}/></label>
 <label>Reviewer notes and unresolved provisions<textarea className={cls} value={notes} onChange={e=>setNotes(e.target.value)}/></label>
 <label className="flex gap-2"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>This is the reviewer's actual supplied declaration; credentials are not verified by KRAFZEN.</label>
 <button type="button" disabled={busy||!confirmed||name.trim().length<2||credential.trim().length<2||reference.trim().length<3||notes.trim().length<10} className="rounded border border-white/20 p-2 disabled:opacity-40" onClick={()=>void submit()}>{busy?"Recording…":"Record review declaration"}</button>
 {error&&<p role="alert">{error}</p>}</>:<p>No independent review declaration is available.</p>}
 </section>;
}
