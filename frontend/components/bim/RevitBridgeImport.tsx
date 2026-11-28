"use client";
import {useState} from "react";
import {importRevitBridge} from "@/lib/api/api";
export default function RevitBridgeImport({user,jobId,onSaved}:{user:User|null;jobId:string;onSaved:()=>void}){
 const [rvt,setRvt]=useState<File|null>(null),[ifc,setIfc]=useState<File|null>(null);
 const [confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState(""),[error,setError]=useState("");
 async function submit(){
  if(!user||!rvt||!ifc||!confirmed||busy)return;
  setBusy(true);setError("");setMessage("");
  try{
   if(!rvt.name.toLowerCase().endsWith(".rvt")||!ifc.name.toLowerCase().endsWith(".ifc")||
      [rvt,ifc].some(f=>!f.size||f.size>40*1024*1024))throw Error("Select original RVT and actual exported IFC, each at most 40 MB.");
   const r=await importRevitBridge(user,jobId,rvt,ifc);
   if(!r.ok)throw Error(r.error?.message||"Revit bridge import failed");
   setMessage("IFC parsed and saved. RVT/IFC hashes recorded; source relationship is user-declared.");onSaved();
  }catch(e){setError(e instanceof Error?e.message:"Import failed");}
  finally{setBusy(false);}
 }
 return <section className="rounded-xl border border-white/10 p-4 space-y-3 text-sm">
  <h2 className="font-semibold">Revit (RVT) desktop bridge</h2>
  <p className="text-slate-400">Open and save the model in Autodesk Revit. Use File → Export → IFC (IFC4 or IFC2x3), then select that IFC and the matching saved RVT below. Both files are scanned; only parsed IFC is stored for BIM analysis. Keep the original RVT locally. Native RVT parsing and conversion fidelity are not independently verified.</p>
  <label className="block">Original RVT<input type="file" accept=".rvt" disabled={busy} onChange={e=>{setRvt(e.target.files?.[0]||null);setConfirmed(false);}} className="block w-full"/></label>
  <label className="block">Revit-exported IFC<input type="file" accept=".ifc" disabled={busy} onChange={e=>{setIfc(e.target.files?.[0]||null);setConfirmed(false);}} className="block w-full"/></label>
  <label className="flex gap-2"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>I confirm that the IFC was exported from this exact saved RVT revision.</label>
  <button type="button" disabled={!rvt||!ifc||!confirmed||busy} onClick={()=>void submit()} className="rounded border border-white/20 p-2 disabled:opacity-40">{busy?"Scanning and importing…":"Import Revit model through IFC"}</button>
  {error&&<p role="alert" className="text-red-300">{error}</p>}
  {message&&<p role="status" className="text-emerald-300">{message}</p>}
 </section>;
}
