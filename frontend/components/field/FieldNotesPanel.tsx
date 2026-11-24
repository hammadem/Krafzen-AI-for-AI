"use client";
import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api/utils";

type Note = {id:string; kind:"comment"|"corrective_action"|"progress_update";body:string;due_date?:string|null;created_at:string};
export default function FieldNotesPanel({inspectionId,user}:{inspectionId:string;user:User|null}) {
    const [open,setOpen]=useState(false);
    const [notes,setNotes]=useState<Note[]>([]);
    const [kind,setKind]=useState<Note["kind"]>("comment");
    const [body,setBody]=useState("");
    const [due,setDue]=useState("");
    const [busy,setBusy]=useState(false);
    const [error,setError]=useState("");
    const [loading,setLoading]=useState(false);
    const [hasMore,setHasMore]=useState(false);
    const endpoint=`${getApiBaseUrl().replace(/\/$/,"")}/api/v1/field/inspections/${encodeURIComponent(inspectionId)}/notes`;
    async function request(init?:RequestInit, offset=0) {
        if(!user?.access_token) throw new Error("Authentication required");
        const res=await fetch(endpoint+(init?.method==="POST"?"":`?limit=50&offset=${offset}`),{
            ...init,headers:{Authorization:`Bearer ${user.access_token}`,apikey:process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY||"","Content-Type":"application/json"}
        });
        const payload=await res.json().catch(()=>({}));
        if(!res.ok) throw new Error(typeof payload.detail==="string"?payload.detail:"Observation note request failed");
        return payload;
    }
    useEffect(()=>{
        if(!open||!user?.access_token)return;
        let active=true;setLoading(true);setError("");
        void request().then(data=>{
            if(!Array.isArray(data))throw new Error("Invalid observation note response");
            if(active){setNotes(data);setHasMore(data.length===50);}
        }).catch(e=>{if(active)setError(e instanceof Error?e.message:"Notes unavailable");}).finally(()=>{if(active)setLoading(false);});
        return()=>{active=false;};
        // eslint-disable-next-line react-hooks/exhaustive-deps
    },[open,inspectionId,user?.access_token]);
    async function save(){
        if(!body.trim()||busy)return;
        setBusy(true);setError("");
        try{
            const saved=await request({method:"POST",body:JSON.stringify({kind,body:body.trim(),due_date:kind==="corrective_action"&&due?due:null})});
            if(!saved?.id)throw new Error("Server did not confirm note persistence");
            setNotes(old=>[saved,...old]);setBody("");setDue("");
        }catch(e){setError(e instanceof Error?e.message:"Note not saved");}
        finally{setBusy(false);}
    }
    async function more(){
        setLoading(true);setError("");
        try{const batch=await request(undefined,notes.length);if(!Array.isArray(batch))throw new Error("Invalid notes response");setNotes(old=>[...old,...batch]);setHasMore(batch.length===50);}
        catch(e){setError(e instanceof Error?e.message:"Notes unavailable");}
        finally{setLoading(false);}
    }
    return <div className="border-t border-white/10 pt-3 space-y-2 text-sm">
        <button type="button" className="underline" onClick={()=>setOpen(v=>!v)}>{open?"Hide observation notes":"Comments and corrective actions"}</button>
        {open&&<>
            <p className="text-xs text-slate-400">Saved owner-authored notes. Corrective action records do not automatically resolve or verify an inspection.</p>
            <label className="block">Note type<select className="ml-2 rounded bg-slate-900 border border-white/20 p-1" value={kind} onChange={e=>setKind(e.target.value as Note["kind"])}><option value="comment">Comment</option><option value="corrective_action">Corrective action</option><option value="progress_update">Progress update</option></select></label>
            {kind==="corrective_action"&&<label className="block">Target date (optional)<input type="date" value={due} onChange={e=>setDue(e.target.value)} className="ml-2 rounded bg-slate-900 border border-white/20 p-1"/></label>}
            <textarea aria-label="Observation note" className="w-full rounded bg-slate-900 border border-white/20 p-2" rows={3} maxLength={4000} value={body} onChange={e=>setBody(e.target.value)}/>
            <button type="button" disabled={busy||!body.trim()} onClick={()=>void save()} className="rounded bg-emerald-300 px-3 py-2 text-slate-950 disabled:opacity-40">{busy?"Saving…":"Save note"}</button>
            {error&&<p role="alert" className="text-red-300">{error}</p>}
            {loading&&<p role="status">Loading notes…</p>}
            {notes.map(n=><div key={n.id} className="rounded border border-white/10 p-2"><p className="text-xs text-slate-400">{n.kind.replaceAll("_"," ")} · {new Date(n.created_at).toLocaleString()}{n.due_date?` · Due ${n.due_date}`:""}</p><p className="whitespace-pre-wrap break-words">{n.body}</p></div>)}
            {hasMore&&<button type="button" disabled={loading} onClick={()=>void more()} className="underline">Load older notes</button>}
        </>}
    </div>;
}
