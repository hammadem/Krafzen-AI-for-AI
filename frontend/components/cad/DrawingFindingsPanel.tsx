"use client";
import {useEffect,useRef,useState} from "react";
import {getApiBaseUrl} from "@/lib/api/utils";
import {createDrawingRedline} from "@/lib/api/api";
type Finding={kind:string;layer:string;handles:string[];x:number;y:number;message:string;recommendation:string;severity:string};
type Report={file_id:string;source_sha256:string;file_version:number;checked_line_count:number;unchecked_entity_count:number;dimension_entity_count:number;text_entity_count:number;finding_count:number;findings:Finding[];truncated:boolean;limitations:string};
export default function DrawingFindingsPanel({user,fileId,onSaved}:{user:User|null;fileId:string;onSaved:()=>void}){
 const scope=fileId+":"+(user?.userId||"")+":"+(user?.access_token||"");
 const current=useRef(scope);current.current=scope;
 const [report,setReport]=useState<Report|null>(null),[reportScope,setReportScope]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
 useEffect(()=>{setReport(null);setBusy(false);setError("");},[scope]);
 async function analyze(){
  if(!user?.access_token||!fileId||busy)return;
  const start=scope;setBusy(true);setError("");setReport(null);
  try{
   const res=await fetch(getApiBaseUrl().replace(/\/$/,"")+"/api/v1/reviews/files/"+encodeURIComponent(fileId)+"/findings",{headers:{Authorization:"Bearer "+user.access_token,apikey:process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY||""}});
   const data=await res.json();
   if(!res.ok||data.file_id!==fileId||!Array.isArray(data.findings)||!data.source_sha256)throw Error(typeof data.detail==="string"?data.detail:"Drawing findings unavailable");
   if(current.current===start){setReport(data);setReportScope(start);}
  }catch(e){if(current.current===start)setError(e instanceof Error?e.message:"Review failed");}
  finally{if(current.current===start)setBusy(false);}
 }
 async function save(f:Finding){
  if(!user||!report||reportScope!==scope||busy)return;
  if(!window.confirm("Save this observed geometry finding as a human-reviewed redline?"))return;
  const start=scope;setBusy(true);setError("");
  try{
   const comment=(f.message+" "+f.recommendation+" Layer: "+f.layer+"; source handles: "+f.handles.join(", ")+"; SHA-256: "+report.source_sha256).slice(0,2000);
   const result=await createDrawingRedline(user,fileId,{kind:"comment",x:f.x,y:f.y,comment,severity:f.severity});
   if(!result.ok)throw Error(result.error?.message||"Could not save review finding");
   if(current.current===start)onSaved();
  }catch(e){if(current.current===start)setError(e instanceof Error?e.message:"Save failed");}
  finally{if(current.current===start)setBusy(false);}
 }
 return <section className="rounded-xl border border-white/10 p-4 space-y-3 text-sm">
  <h2 className="font-semibold">Source geometry review</h2>
  <button type="button" disabled={!fileId||busy} onClick={()=>void analyze()} className="rounded border border-white/20 p-2 disabled:opacity-40">{busy?"Processing…":"Inspect drawing geometry"}</button>
  {error&&<p role="alert" className="text-amber-300">{error}</p>}
  {report&&reportScope===scope&&<><p>{report.checked_line_count} lines checked · {report.unchecked_entity_count} other entities not checked · {report.finding_count} observations</p>
  <p>{report.dimension_entity_count} DIMENSION entities · {report.text_entity_count} text entities</p>
  <p className="text-xs text-slate-400">{report.limitations}</p>
  {report.truncated&&<p>First 100 findings shown.</p>}
  {report.findings.map((f,i)=><article key={i} className="rounded border border-white/10 p-3"><p>{f.message}</p><p className="text-xs text-slate-400">Layer: {f.layer} · Handles: {f.handles.join(", ")}</p><p>{f.recommendation}</p><button type="button" className="underline" disabled={busy} onClick={()=>void save(f)}>Accept as redline</button></article>)}
  </>}
 </section>
}
