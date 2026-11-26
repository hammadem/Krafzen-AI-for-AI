"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useApiResource } from "@/hooks/useApiResource";
import { getPlatformResidencyEvidence, listWorkspaces, getOrganizationResidency, requestOrganizationUsResidency } from "@/lib/api/api";

type Evidence = { requested_region: string; residency_verified: boolean; evidence_recorded_at: string | null; paths: {name: string; status: string; location?: string | null; detail: string}[] };

export default function ResidencyPage() {
    const {user} = useAuth();
    const [workspaceId, setWorkspaceId] = useState("");
    const [requesting, setRequesting] = useState(false);
    const [notice, setNotice] = useState("");
    const workspaces = useApiResource<{id:string; name:string; owner_id:string}[]>({
        fetcher: u => listWorkspaces(u),
        select: raw => Array.isArray(raw) ? raw as unknown as {id:string;name:string;owner_id:string}[] : [],
        fallback: [], enabled: !!user?.access_token,
    });
    const workspace = workspaces.data.find(w=>w.id===workspaceId);
    const assignment = useApiResource<{status:string; region_code:string; residency_verified:boolean} | null>({
        fetcher: u=>getOrganizationResidency(u, workspaceId),
        select: raw=>raw as unknown as {status:string;region_code:string;residency_verified:boolean},
        fallback:null, enabled: !!workspaceId && !!user?.access_token, resourceKey:workspaceId,
    });
    async function request() {
        if (!user || !workspace || requesting) return;
        if (!window.confirm("Request US residency? Regional operations may remain blocked while infrastructure is provisioned.")) return;
        setRequesting(true);setNotice("");
        try {
            const result = await requestOrganizationUsResidency(user, workspace.id);
            setNotice(result.ok ? "Residency request recorded. This is not a verified activation." : result.error?.message || "Request failed.");
            assignment.refetch();
        } catch {setNotice("Residency service unavailable.");}
        finally {setRequesting(false);}
    }
    const {data, isLoading, isError, error, refetch} = useApiResource<Evidence | null>({
        fetcher: u => getPlatformResidencyEvidence(u),
        select: raw => raw as unknown as Evidence,
        fallback: null,
        enabled: !!user?.access_token,
    });
    return <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white space-y-5">
        <h1 className="text-2xl font-semibold">USA Data Residency</h1>
        <p className="text-slate-400">Provider location evidence and end-to-end processing coverage.</p>
        <button onClick={refetch} disabled={isLoading} className="rounded border border-white/20 px-3 py-2">Refresh evidence</button>
        {isLoading && <p role="status">Loading residency evidence…</p>}
        {isError && <p role="alert">{error?.message || "Residency evidence unavailable"}</p>}
        <section className="rounded-xl border border-white/10 p-4 space-y-3">
            <h2 className="font-semibold">Enterprise organization residency</h2>
            <label className="block text-sm">Organization
                <select value={workspaceId} onChange={e=>{setWorkspaceId(e.target.value);setNotice("");}} className="mt-1 block w-full rounded border border-white/20 bg-slate-900 p-2">
                    <option value="">Select a workspace</option>
                    {workspaces.data.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
            </label>
            {workspaces.isError && <p role="alert">Could not load organizations.</p>}
            {assignment.isLoading && workspaceId && <p>Loading assignment…</p>}
            {assignment.isError && workspaceId && <p className="text-amber-200">{assignment.error?.message || "No readable residency assignment."}</p>}
            {assignment.data && !assignment.isLoading && <p>Recorded assignment: {assignment.data.region_code} / {assignment.data.status}. End-to-end verification outstanding.</p>}
            {workspace?.owner_id===user?.userId && workspace && <button type="button" disabled={requesting} onClick={()=>void request()} className="rounded border border-white/20 px-3 py-2">Request USA residency (Enterprise)</button>}
            {notice && <p role="status">{notice}</p>}
            <p className="text-xs text-slate-400">This requests provisioning only; it does not migrate data, enable billing or establish certification.</p>
        </section>
        {data && !isError && !isLoading && <>
            <p className="rounded-lg border border-amber-400/30 p-4 text-amber-200">End-to-end USA data residency is not certified. Provider locations alone cannot establish where every data-processing path runs.</p>
            <p className="text-sm text-slate-400">Recorded provider evidence: {data.evidence_recorded_at || "Not recorded"}</p>
            <div className="grid gap-3 sm:grid-cols-2">{data.paths.map(path=><article key={path.name} className="rounded-xl border border-white/10 p-4 space-y-2">
                <h2 className="font-semibold">{path.name}</h2>
                <p className={path.status==="provider_region_recorded"?"text-emerald-300":"text-amber-300"}>{path.status==="provider_region_recorded"?"Provider location recorded":"Verification outstanding"}{path.location && " · "+path.location}</p>
                <p className="text-sm text-slate-400">{path.detail}</p>
            </article>)}</div>
        </>}
    </main>;
}
