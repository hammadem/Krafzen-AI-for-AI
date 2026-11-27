"use client";
import {useApiResource} from "@/hooks/useApiResource";
import {apiClient} from "@/lib/api/utils";
type Capabilities={scanner_prerequisites_detected:boolean;private_scanner_self_test_verified:boolean;dwg_engine:string;dwg_runtime_available:boolean;ocr_engine_detected:boolean;revit_native_conversion_available:boolean;revit_ifc_bridge_implemented:boolean;customer_upload_verified:boolean};
function select(raw:unknown):Capabilities{
 const r=raw as Capabilities;
 if(!r||typeof r.scanner_prerequisites_detected!=="boolean"||typeof r.dwg_runtime_available!=="boolean"||typeof r.ocr_engine_detected!=="boolean")throw Error("Invalid runtime evidence");
 return r;
}
export default function ImportRuntimeEvidence(){
 const {data,isLoading,isError,error,refetch}=useApiResource<Capabilities|null>({fetcher:user=>apiClient("GET","/api/v1/files/capabilities",user),select,fallback:null});
 return <section className="rounded-xl border border-white/10 p-4 space-y-2 text-sm" aria-label="Import runtime evidence">
 <div className="flex justify-between gap-2 items-center"><h2 className="font-semibold">Import runtime evidence</h2><button type="button" onClick={refetch} disabled={isLoading} className="underline">Refresh capabilities</button></div>
 {isLoading&&<p role="status">Checking import prerequisites…</p>}
 {isError&&<p role="alert">{error?.message||"Could not verify import capabilities."}</p>}
 {data&&!isLoading&&!isError&&<>
 <p className={data.scanner_prerequisites_detected?"text-emerald-300":"text-amber-200"}>{data.scanner_prerequisites_detected?"Scanner prerequisites detected; every upload still requires an actual clean scan.":"Scanner unavailable or signatures unverified — protected uploads will be rejected."}</p>
 {data.private_scanner_self_test_verified&&<p>Private scanner benign/EICAR self-test verified.</p>}
 <p>DWG: {data.dwg_engine} · {data.dwg_runtime_available?"native runtime detected":"runtime unavailable"}; actual conversion must validate.</p>
 <p>Drawing OCR: {data.ocr_engine_detected?"Tesseract executable detected":"engine unavailable"}.</p>
 <p>Revit: local IFC exchange implemented; native server RVT conversion unavailable.</p>
 <p className="text-slate-400 text-xs">Runtime checks are not proof of a successful customer upload or complete model fidelity. Server-side authorization and scanning remain mandatory.</p>
 </>}
 </section>;
}
