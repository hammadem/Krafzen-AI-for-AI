"use client";
import Link from "next/link";
import {useApiResource} from "@/hooks/useApiResource";
import {getAecModelRegistry} from "@/lib/api/api";
type Model={name:string;mode:string;runtime_available:boolean;training_count?:number;evaluation_count?:number;correct?:number;baseline_correct?:number;scope:string;workspace_path?:string;workflow_run?:string;artifact?:string;artifact_retention_days?:number;source_sha256?:string};
type Source={name:string;url:string;license:string;commercial_use:string;format:string;category:string;processing:string;training_use:string;version:string};
type Reference={dataset_id:string;title:string;schema:string;source_url:string;sha256:string;license:string};
type Registry={reference_count:number;references:Reference[];datasets:Source[];models:Model[];scope:string};
function select(raw:unknown):Registry{
 const data=raw as Registry;
 if(!data||!Array.isArray(data.models)||!Array.isArray(data.datasets)||!Array.isArray(data.references)||typeof data.reference_count!=="number")throw Error("Invalid model registry");
 return data;
}
export default function AiKnowledge(){
 const {data,isLoading,isError,error,refetch}=useApiResource<Registry|null>({fetcher:getAecModelRegistry,select,fallback:null});
 return <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white space-y-5">
 <h1 className="text-2xl font-semibold">AI &amp; Knowledge Evidence</h1>
 <p className="text-slate-400">Actual model evaluation records, approved source references and dataset rights. Experimental results are not engineering approval.</p>
 <button type="button" className="rounded border border-white/20 px-3 py-2" disabled={isLoading} onClick={refetch}>Refresh model evidence</button>
 {isLoading&&<p role="status">Loading model evidence…</p>}
 {isError&&<p role="alert">{error?.message||"Model evidence unavailable"}</p>}
 {data&&!isLoading&&!isError&&<>
 <section className="grid gap-3 md:grid-cols-2">{data.models.map(m=><article key={m.name} className="rounded-xl border border-white/10 p-4 space-y-2">
 <h2 className="font-semibold">{m.name}</h2>
 <p className={m.runtime_available?"text-emerald-300":"text-amber-200"}>{m.runtime_available?"Runtime path available (scope limited)":"Runtime not enabled"}</p>
 <p className="text-xs text-slate-400">{m.mode.replaceAll("_"," ")}</p>
 {m.training_count!==undefined&&<p>Training: {m.training_count} · Evaluation: {m.evaluation_count} · Correct: {m.correct}/{m.evaluation_count}</p>}
 {m.baseline_correct!==undefined&&<p>Baseline: {m.baseline_correct}/{m.evaluation_count}</p>}
 <p className="text-sm">{m.scope}</p>
 {m.workspace_path&&<Link className="underline" href={m.workspace_path}>Open workflow</Link>}
 {m.workflow_run&&<a className="block underline" href={m.workflow_run} target="_blank" rel="noreferrer">Training run evidence</a>}
 {m.artifact&&<a className="block underline" href={m.artifact} target="_blank" rel="noreferrer">Experimental adapter and metrics ({m.artifact_retention_days}-day CI retention)</a>}
 </article>)}</section>
 <section className="rounded-xl border border-white/10 p-4 space-y-3"><h2 className="font-semibold">Approved IFC references ({data.reference_count})</h2>
 {data.references.map(row=><details key={row.dataset_id} className="border-b border-white/10 pb-2 text-sm"><summary>{row.title} · {row.schema}</summary><p>{row.license}</p><p className="break-all text-xs">SHA-256: {row.sha256}</p><a className="underline" href={row.source_url} target="_blank" rel="noreferrer">Original source</a></details>)}
 </section>
 <section className="rounded-xl border border-white/10 p-4 space-y-3"><h2 className="font-semibold">Dataset license register</h2>
 {data.datasets.map(source=><details key={source.name} className="border-b border-white/10 pb-2 text-sm"><summary>{source.name} · {source.license}</summary><p>Rights: {source.commercial_use}</p><p>Processing: {source.processing}</p><p>Training: {source.training_use}</p><p>Version: {source.version}</p>{source.url.startsWith("https://")&&<a className="underline" href={source.url} target="_blank" rel="noreferrer">Publisher source</a>}</details>)}
 </section><p className="text-xs text-slate-400">{data.scope}</p>
 </>}
 </main>;
}
