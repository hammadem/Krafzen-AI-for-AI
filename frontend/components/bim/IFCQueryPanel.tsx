"use client";
import {useState} from "react";
import {queryIfcSource} from "@/lib/api/api";
type Evidence = {file_id:string;project_id:string;source_sha256:string;result:Record<string,unknown>};
const modes = [["count","How many elements?"],["elements","Which elements are in a floor?"],["properties","What properties does this element have?"],["missing_property","Which elements lack a declared property?"],["quantity","What is the declared quantity total?"]];
const classes=["IfcElement","IfcWall","IfcSlab","IfcDoor","IfcWindow","IfcSpace","IfcColumn","IfcBeam","IfcStair","IfcRoof","IfcDistributionElement"];
export default function IFCQueryPanel({user,fileId}:{user:User|null;fileId:string}) {
    const [mode,setMode]=useState("count");
    const [kind,setKind]=useState("IfcWall");
    const [storey,setStorey]=useState("");
    const [guid,setGuid]=useState("");
    const [setName,setSetName]=useState("");
    const [property,setProperty]=useState("");
    const [evidence,setEvidence]=useState<Evidence|null>(null);
    const [busy,setBusy]=useState(false);
    const [error,setError]=useState("");
    const r=evidence?.result;
    const storeys=Array.isArray(r?.storeys)?r.storeys as {guid:string;name:string}[]:[];
    const elements=Array.isArray(r?.elements)?r.elements as {guid:string;name:string;ifc_type:string}[]:[];
    return <section className="rounded-xl border border-white/10 p-5 space-y-3">
        <h2 className="font-semibold">Ask the source IFC model</h2>
        <p className="text-sm text-slate-400">Choose a supported question. Results are extracted directly from the selected IFC file, not guessed by an AI model.</p>
        <form className="space-y-3" onSubmit={async e=>{
            e.preventDefault();if(busy||!user)return;
            setBusy(true);setError("");
            try {
                const response=await queryIfcSource(user,fileId,{mode,entity_class:kind,...(storey?{storey_guid:storey}:{}),...(guid?{element_guid:guid}:{}),...(setName.trim()?{set_name:setName.trim()}:{}),...(property.trim()?{property_name:property.trim()}: {})});
                if(!response.ok) throw new Error(response.error?.message||"Source query failed");
                const value=response.data as unknown as Evidence;
                if(value.file_id!==fileId||value.result?.method!=="ifc_source_query_v1")throw new Error("Source evidence did not match selected model");
                setEvidence(value);
            }catch(e){setEvidence(null);setError(e instanceof Error?e.message:"Source query failed");}
            finally{setBusy(false);}
        }}>
            <label className="block text-sm">Model question<select className="block w-full bg-slate-900 border rounded p-2" value={mode} onChange={e=>setMode(e.target.value)}>{modes.map(([v,l])=><option value={v} key={v}>{l}</option>)}</select></label>
            {mode!=="properties"&&<><label className="block text-sm">IFC element class<select className="block w-full bg-slate-900 border rounded p-2" value={kind} onChange={e=>setKind(e.target.value)}>{classes.map(v=><option key={v}>{v}</option>)}</select></label>
            <label className="block text-sm">Storey GlobalId (optional, direct containment)<input maxLength={22} value={storey} onChange={e=>setStorey(e.target.value)} className="block w-full bg-slate-900 border rounded p-2"/></label>
            {!!storeys.length&&<div className="flex gap-2 flex-wrap">{storeys.map(f=><button key={f.guid} type="button" className="text-xs underline" onClick={()=>setStorey(f.guid)}>{f.name||f.guid}</button>)}</div>}</>}
            {mode==="properties"&&<label className="block text-sm">Element GlobalId<input required minLength={22} maxLength={22} value={guid} onChange={e=>setGuid(e.target.value)} className="block w-full bg-slate-900 border rounded p-2"/></label>}
            {(mode==="quantity"||mode==="missing_property")&&<><label className="block text-sm">Exact property or quantity set name<input required maxLength={120} value={setName} onChange={e=>setSetName(e.target.value)} className="block w-full bg-slate-900 border rounded p-2"/></label><label className="block text-sm">Exact property or quantity name<input required maxLength={120} value={property} onChange={e=>setProperty(e.target.value)} className="block w-full bg-slate-900 border rounded p-2"/></label></>}
            <button disabled={busy||!user} className="rounded bg-emerald-300 text-slate-950 px-4 py-2 text-sm font-semibold disabled:opacity-40">{busy?"Reading IFC…":"Query source model"}</button>
        </form>
        {error&&<p role="alert" className="text-red-300">{error}</p>}
        {evidence&&r&&<div className="space-y-2">
            <p className="font-medium">Source result: {String(r.status)}</p>
            {typeof r.match_count==="number"&&<p>Matching entities: {r.match_count}</p>}
            {typeof r.missing_count==="number"&&<p>Missing declarations: {r.missing_count}</p>}
            {elements.map(e=><button key={e.guid} type="button" onClick={()=>{setGuid(e.guid);setMode("properties");}} className="block text-left text-xs underline">{e.name||e.guid} · {e.ifc_type}</button>)}
            <details><summary className="cursor-pointer text-sm">Full source evidence</summary><pre className="text-xs whitespace-pre-wrap break-all max-h-72 overflow-auto">{JSON.stringify(r,null,2)}</pre></details>
            <p className="text-xs break-all text-slate-400">Source SHA-256: {evidence.source_sha256}</p>
            <button type="button" className="text-sm underline" onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(evidence,null,2)],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download="ifc-query-"+fileId+".json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}>Download query evidence</button>
            <p className="text-xs text-amber-200">{String(r.limits)}</p>
        </div>}
    </section>;
}
