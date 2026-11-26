"use client";
import { useAuth } from "@/context/AuthContext";
import { useApiResource } from "@/hooks/useApiResource";
import { getPlatformResidencyEvidence } from "@/lib/api/api";

type Evidence = { requested_region: string; residency_verified: boolean; evidence_recorded_at: string | null; paths: {name: string; status: string; location?: string | null; detail: string}[] };

export default function ResidencyPage() {
    const {user} = useAuth();
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
