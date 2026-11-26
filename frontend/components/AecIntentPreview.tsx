"use client";
import {useRef,useState} from "react";
import {previewAecIntent} from "@/lib/api/api";
type User=Parameters<typeof previewAecIntent>[0];
export default function AecIntentPreview({user,text}:{user:User;text:string}){
 const [result,setResult]=useState<{label:string;confidence:number}|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState("");
 const scope=(user?.userId||"")+":"+(user?.access_token||"")+":"+text;
 const current=useRef(scope);current.current=scope;
 const [resultScope,setResultScope]=useState("");
 async function classify(){
  if(!user||!text.trim()||text.length>2000||busy)return;
  const start=scope;setBusy(true);setError("");setResult(null);setResultScope(start);
  try{const r=await previewAecIntent(user,text);
   if(current.current!==start)return;
   const data=r.data as unknown as {label?:string;confidence?:number;advisory_only?:boolean};
   if(!r.ok||!data?.label||typeof data.confidence!=="number"||!data.advisory_only)throw Error(r.error?.message||"Intent suggestion unavailable");
   setResult({label:data.label,confidence:data.confidence});
  }catch(e){if(current.current===start)setError(e instanceof Error?e.message:"Intent suggestion unavailable");}
  finally{setBusy(false);}
 }
 return <div className="flex flex-wrap gap-2 items-center mb-2 text-xs text-gray-400">
 <button type="button" className="rounded border border-white/20 px-2 py-1 disabled:opacity-40" onClick={()=>void classify()} disabled={busy||!text.trim()||text.length>2000}>{busy?"Classifying…":"Suggest AEC task"}</button>
 {resultScope===scope&&result&&<span role="status">{result.label==="unknown"?"No reliable suggestion":`Suggested task: ${result.label}`} · advisory only</span>}
 {resultScope===scope&&error&&<span role="alert">{error}</span>}
 </div>
}
