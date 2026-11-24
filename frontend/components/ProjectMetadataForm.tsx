"use client";
import { useState } from "react";
const types: ProjectType[] = ["residential","commercial","industrial","institutional","infrastructure","mixed_use","other"];
const stages: ProjectStage[] = ["draft","in_progress","in_review","completed"];

export default function ProjectMetadataForm({project,onClose,onSave}:{project?:ProjectDetails;onClose:()=>void;onSave:(data:ProjectMetadata)=>Promise<void>}) {
    const [title,setTitle]=useState(project?.title || project?.input_text?.slice(0,160) || "");
    const [description,setDescription]=useState(project?.description || "");
    const [type,setType]=useState<ProjectType | "">(project?.project_type || "");
    const [stage,setStage]=useState<ProjectStage>(project?.lifecycle_stage || "draft");
    const [busy,setBusy]=useState(false);
    const [error,setError]=useState("");
    return <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
        <form role="dialog" aria-modal="true" aria-label={project?"Edit project details":"Create project"} className="bg-[#111722] rounded-xl p-6 w-full max-w-lg text-white space-y-4 max-h-[90vh] overflow-auto"
          onSubmit={async e=>{
            e.preventDefault();if(busy)return;
            if(!title.trim()){setError("Enter a project name.");return;}
            setBusy(true);setError("");
            try{await onSave({title:title.trim(),description:description.trim(),project_type:type||null,lifecycle_stage:stage});}
            catch(e){setError(e instanceof Error?e.message:"Project could not be saved.");}
            finally{setBusy(false);}
          }}>
          <h2 className="font-semibold text-lg">{project?"Edit project details":"Create project"}</h2>
          <label className="block text-sm">Project name<input required maxLength={160} value={title} onChange={e=>setTitle(e.target.value)} className="block w-full mt-1 p-2 rounded border border-white/20 bg-black"/></label>
          <label className="block text-sm">Description<textarea maxLength={8000} rows={4} value={description} onChange={e=>setDescription(e.target.value)} className="block w-full mt-1 p-2 rounded border border-white/20 bg-black"/></label>
          <label className="block text-sm">Project type<select value={type} onChange={e=>setType(e.target.value as ProjectType|"")} className="block w-full mt-1 p-2 rounded border border-white/20 bg-black"><option value="">Unclassified</option>{types.map(t=><option key={t} value={t}>{t.replaceAll("_"," ")}</option>)}</select></label>
          <label className="block text-sm">Project stage<select value={stage} onChange={e=>setStage(e.target.value as ProjectStage)} className="block w-full mt-1 p-2 rounded border border-white/20 bg-black">{stages.map(t=><option key={t} value={t}>{t.replaceAll("_"," ")}</option>)}</select></label>
          <p className="text-xs text-slate-400">Stage is your project-management status, not engineering approval.</p>
          {error&&<p role="alert" className="text-red-300">{error}</p>}
          <div className="flex justify-end gap-4"><button type="button" disabled={busy} onClick={onClose}>Cancel</button><button disabled={busy} className="rounded bg-[#54e3b5] text-black px-4 py-2 font-semibold">{busy?"Saving…":project?"Save details":"Create project"}</button></div>
        </form>
    </div>;
}
