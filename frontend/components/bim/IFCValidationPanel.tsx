"use client";
import { useState } from "react";
import { runIfcModelValidation, getIfcModelValidations } from "@/lib/api/api";

type Diagnostic = {category:string; severity:string; step_id:number|null; guid:string|null; ifc_type:string|null; message:string};
type Element = {step_id:number; guid:string|null; ifc_type:string; name:string; container_name:string; declared_properties:Record<string,Record<string,unknown>>};
type RecordRow = {id:string; file_id:string; source_sha256:string; created_at:string; result:{
    method:string; schema:string; finding_count:number; finding_counts:Record<string,number>; findings:Diagnostic[];
    element_count:number; geometry_checked_count:number; geometry_failed_count:number; represented_count:number;
    declared_port_count:number; declared_connected_port_count:number; physical_class_counts:Record<string,number>;
    element_inventory:Element[]; inventory_truncated:boolean; analysis_partial:boolean; limitations:string;
}};
type Props = {user:Parameters<typeof runIfcModelValidation>[0]; fileId:string};

export default function IFCValidationPanel({user,fileId}:Props) {
    const [rows,setRows]=useState<RecordRow[]>([]);
    const [selected,setSelected]=useState<RecordRow|null>(null);
    const [query,setQuery]=useState("");
    const [busy,setBusy]=useState(false);
    const [error,setError]=useState("");
    async function act(create:boolean) {
        if (busy || !user || !fileId) return;
        setBusy(true);setError("");
        try {
            const response=create?await runIfcModelValidation(user,fileId):await getIfcModelValidations(user,fileId);
            if(!response.ok) throw new Error(response.error?.message || "IFC validation evidence unavailable");
            const found=(create?[response.data]:response.data) as RecordRow[];
            if(!Array.isArray(found)||found.some(row=>row.file_id!==fileId||row.result?.method!=="ifcopenshell_source_validation_v1")) {
                throw new Error("Unexpected validation record");
            }
            setRows(previous=>create?[...found,...previous.filter(r=>r.id!==found[0]?.id)]:found);
            setSelected(found[0]||null);
        }catch(e){setError(e instanceof Error?e.message:"Validation failed");}
        finally{setBusy(false);}
    }
    const r=selected?.result;
    const filtered=r?.element_inventory.filter(e=>[e.name,e.guid,e.ifc_type,e.container_name].some(v=>String(v||"").toLowerCase().includes(query.trim().toLowerCase())))||[];
    return <section className="space-y-3 rounded-xl border border-white/10 p-5">
        <h2 className="font-semibold">Source IFC model validation and property inspector</h2>
        <p className="text-sm text-amber-200">Actual schema and parser diagnostics, duplicate GlobalIds, native geometry checks, declared spatial containment and port relationships. This does not certify full model validity or MEP system operation.</p>
        <div className="flex flex-wrap gap-2">
            <button type="button" disabled={busy} onClick={()=>void act(true)} className="rounded bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">{busy?"Working…":"Run and save IFC validation"}</button>
            <button type="button" disabled={busy} onClick={()=>void act(false)} className="rounded border border-white/20 px-4 py-2 text-sm">Load saved validation history</button>
        </div>
        {error&&<p role="alert" className="text-red-300 text-sm">{error}</p>}
        {rows.map(row=><button key={row.id} type="button" onClick={()=>setSelected(row)} className="block text-left text-sm underline">{row.created_at} · {row.result.finding_count} observations</button>)}
        {r&&selected&&<div className="space-y-3">
            <p>{r.schema} · {r.element_count} elements · {r.finding_count} observations</p>
            <p className="text-sm">Geometry: {r.geometry_checked_count}/{r.represented_count} represented elements checked; {r.geometry_failed_count} could not be tessellated.</p>
            <p className="text-sm">Declared connected ports: {r.declared_connected_port_count}/{r.declared_port_count}</p>
            {r.analysis_partial&&<p className="text-amber-200 text-sm">Partial analysis: some model elements exceed the bounded inspection budget.</p>}
            <p className="break-all text-xs text-slate-400">SHA-256: {selected.source_sha256}</p>
            <button type="button" onClick={()=>{
                const url=URL.createObjectURL(new Blob([JSON.stringify(selected,null,2)],{type:"application/json"}));
                const link=document.createElement("a");link.href=url;link.download=`ifc-validation-${selected.id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
            }} className="text-sm underline">Download saved IFC validation evidence</button>
            <h3 className="font-semibold">Observed finding categories</h3>
            {Object.entries(r.finding_counts).map(([k,v])=><p key={k} className="text-sm">{k.replaceAll("_"," ")}: {v}</p>)}
            <div className="max-h-64 overflow-auto space-y-2">
                {r.findings.map((x,i)=><p key={i} className="border-b border-white/10 py-1 text-xs">{x.severity} · {x.ifc_type} #{x.step_id} {x.guid} — {x.message}</p>)}
            </div>
            <h3 className="font-semibold">Actual IFC element inventory and properties</h3>
            <input aria-label="Search IFC elements" placeholder="Search name, GlobalId, type or floor" value={query} onChange={e=>setQuery(e.target.value)} className="w-full rounded border border-white/20 bg-slate-900 p-2 text-sm"/>
            {r.inventory_truncated&&<p className="text-xs text-amber-200">Element inventory is bounded. Use the original model for complete inspection.</p>}
            <div className="max-h-96 overflow-auto space-y-2">
                {filtered.slice(0,50).map(e=><details key={e.step_id} className="border border-white/10 rounded p-2">
                    <summary className="cursor-pointer text-sm">{e.ifc_type} {e.name||e.guid||e.step_id} · {e.container_name||"No resolved container"}</summary>
                    <p className="text-xs break-all">{e.guid}</p>
                    <pre className="overflow-x-auto whitespace-pre-wrap break-all text-xs text-slate-300">{JSON.stringify(e.declared_properties,null,2)}</pre>
                </details>)}
            </div>
            <p className="text-xs text-slate-400">{r.limitations}</p>
        </div>}
    </section>;
}
