"use client";
import {useEffect,useState} from "react";
import {getAllFiles,getFileSignedUrl} from "@/lib/api/api";
import {getApiBaseUrl} from "@/lib/api/utils";
type Source={id:string;name?:string;import_metadata?:{generation_method?:string}};
type Preview={file_id:string;source_sha256:string;geometry:Record<string,unknown>;command:string};
export default function RoomCommandPanel({user,jobId}:{user:User|null;jobId:string}){
 const [sources,setSources]=useState<Source[]>([]),[selected,setSelected]=useState(""),[command,setCommand]=useState(""),[preview,setPreview]=useState<Preview|null>(null),[saved,setSaved]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState(""),[link,setLink]=useState(""),[refresh,setRefresh]=useState(0);
 useEffect(()=>{if(!user||!jobId)return;let active=true;setSources([]);setSelected("");setPreview(null);setSaved("");setLink("");getAllFiles(user,jobId).then(r=>{if(!r.ok)throw Error(r.error?.message||"Unable to load drawings");if(active){const data=Array.isArray(r.data)?r.data as unknown as Source[]:[];setSources(data.filter(f=>f.import_metadata?.generation_method==="parametric_room_v1"));}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[user?.access_token,jobId,refresh]);
 async function edit(apply:boolean){
   if(!user?.access_token||!selected||!command.trim()||busy)return;
   setBusy(true);setError("");setLink("");
   try{
      if(apply&&(!preview||preview.command!==command||preview.file_id!==selected))throw Error("Preview the current command first");
      const res=await fetch(getApiBaseUrl().replace(/\/$/,"")+"/api/v1/cad/rooms/"+encodeURIComponent(selected)+(apply?"/edit":"/edit-preview"),{method:"POST",headers:{Authorization:"Bearer "+user.access_token,"Content-Type":"application/json",apikey:process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY||""},body:JSON.stringify({command,...(apply?{expected_sha256:preview!.source_sha256}:{})})});
      const r=await res.json().catch(()=>({}));if(!res.ok)throw Error(typeof r.detail==="string"?r.detail:"CAD edit rejected");
      if(apply){if(!r.file?.id)throw Error("New drawing not confirmed");setSaved(r.file.id);setPreview(null);setSources(old=>[...old,{id:r.file.id,name:r.file.name,import_metadata:r.geometry}]);setSelected(r.file.id);setCommand("");}
      else{if(r.file_id!==selected||!r.source_sha256)throw Error("Unverified preview");setPreview(r);setSaved("");}
   }catch(e){setError(e instanceof Error?e.message:"CAD edit failed");}finally{setBusy(false);}
 }
 async function download(){
   try{const r=await getFileSignedUrl(user,saved);if(!r.ok)throw Error(r.error?.message||"Download unavailable");const url=new URL((r.data as unknown as {signed_url:string}).signed_url);if(url.protocol!=="https:"||url.username||url.password)throw Error("Unsafe signed URL");setLink(url.toString());}catch(e){setError(e instanceof Error?e.message:"Download failed");}
 }
 return <section className="space-y-3 rounded-xl border border-white/10 p-4 text-sm"><h2 className="font-semibold">Edit an existing parametric drawing by command</h2>
 <p className="text-slate-400">Use explicit dimensions and units. Each accepted edit creates a separate source-linked DXF; original drawings are preserved.</p>
 <button type="button" className="underline" onClick={()=>setRefresh(v=>v+1)}>Refresh generated drawings</button>
 <label className="block">Source drawing<select disabled={busy} value={selected} onChange={e=>{setSelected(e.target.value);setPreview(null);setSaved("");setLink("");}} className="block w-full bg-slate-900 p-2"><option value="">Choose generated room</option>{sources.map(s=><option key={s.id} value={s.id}>{s.name||s.id}</option>)}</select></label>
 <label className="block">Edit command<input disabled={busy} maxLength={500} value={command} onChange={e=>{setCommand(e.target.value);setPreview(null);}} placeholder="set width to 6 m" className="block w-full bg-slate-900 p-2"/></label>
 <p className="text-xs">Examples: set length to 15 ft; add door on south at 1 m width 900 mm; remove opening 1; rename room to Office.</p>
 <button type="button" disabled={busy||!selected||!command.trim()} onClick={()=>void edit(false)} className="rounded border p-2 disabled:opacity-40">Preview edit</button>
 {preview&&<div className="space-y-2"><pre className="whitespace-pre-wrap break-all max-h-64 overflow-auto text-xs">{JSON.stringify(preview.geometry,null,2)}</pre><button type="button" disabled={busy} onClick={()=>void edit(true)} className="rounded bg-emerald-300 text-slate-950 p-2">Confirm and save revised DXF</button></div>}
 {saved&&<div><p role="status">Revised drawing saved. Original retained.</p><button className="underline" type="button" onClick={()=>void download()}>Request private download</button>{link&&<a className="block underline" href={link} target="_blank" rel="noreferrer">Download revised DXF</a>}</div>}
 {error&&<p role="alert" className="text-red-300">{error}</p>}</section>;
}
