"use client";
import {useEffect,useState} from "react";
import {getApiBaseUrl} from "@/lib/api/utils";
type Workspace={id:string;name:string;owner_id:string};
type Member={user_id:string;email?:string;display_name?:string;role:string};
type Task={id:string;project_id:string;project_title:string;title:string;discipline:string;assignee_id:string;assigned_by:string;status:string;can_update:boolean};
const discipline=["architecture","structural","mechanical","electrical","plumbing","site","other"];
export default function ProjectAssignmentsPanel({user,projects}:{user:User|null;projects:ProjectDetails[]}){
 const [open,setOpen]=useState(false),[tasks,setTasks]=useState<Task[]>([]),[workspaces,setWorkspaces]=useState<Workspace[]>([]),[members,setMembers]=useState<Member[]>([]);
 const [project,setProject]=useState(""),[workspace,setWorkspace]=useState(""),[member,setMember]=useState(""),[title,setTitle]=useState(""),[kind,setKind]=useState("architecture"),[error,setError]=useState(""),[busy,setBusy]=useState(false),[offset,setOffset]=useState(0);
 const request=async(path:string,method="GET",body?:object)=>{
   if(!user?.access_token)throw Error("Sign in required");
   const res=await fetch(getApiBaseUrl().replace(/\/$/,"")+"/api/v1"+path,{method,headers:{Authorization:"Bearer "+user.access_token,"Content-Type":"application/json",apikey:process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY||""},...(body?{body:JSON.stringify(body)}:{})});
   const data=await res.json().catch(()=>({}));if(!res.ok)throw Error(typeof data.detail==="string"?data.detail:"Assignment request rejected");return data;
 };
 const load=async(start=offset)=>{const rows=await request("/assignments/?limit=50&offset="+start);if(!Array.isArray(rows))throw Error("Invalid assignment response");setTasks(rows);setOffset(start);};
 useEffect(()=>{if(!open||!user?.access_token)return;let active=true;setError("");Promise.all([request("/assignments/?limit=50&offset=0"),request("/workspaces/")]).then(([rows,ws])=>{if(active){setTasks(rows);setOffset(0);setWorkspaces(ws.filter((w:Workspace)=>w.owner_id===user.userId));}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[open,user?.access_token,user?.userId]);
 useEffect(()=>{setMember("");setMembers([]);if(!workspace||!open)return;let active=true;request("/workspaces/"+encodeURIComponent(workspace)+"/members?page=1&page_size=100").then(r=>{if(active)setMembers(r.members.filter((m:Member)=>m.role==="admin"||m.role==="member"));}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[workspace,open,user?.access_token]);
 async function mutate(path:string,method:string,body?:object){setBusy(true);setError("");try{await request(path,method,body);await load(0);return true;}catch(e){setError(e instanceof Error?e.message:"Assignment operation failed");return false;}finally{setBusy(false);}}
 return <section className="rounded-xl border border-white/10 p-4 space-y-3 text-white text-sm">
   <button type="button" className="underline" onClick={()=>setOpen(v=>!v)}>{open?"Hide project assignments":"Project assignments"}</button>
   {open&&<><p className="text-slate-400">Assign tasks to current contributing members of your workspace. This shares the project title and task only; private drawings, project content and regional storage remain protected.</p>
   {error&&<p role="alert" className="text-red-300">{error}</p>}
   {!!workspaces.length&&<form className="grid gap-2" onSubmit={async e=>{e.preventDefault();if(await mutate("/assignments/","POST",{project_id:project,workspace_id:workspace,assignee_id:member,title,discipline:kind}))setTitle("");}}>
   <label>Owned project<select required className="block w-full bg-slate-900 p-2" value={project} onChange={e=>setProject(e.target.value)}><option value="">Choose project on current page</option>{projects.map(p=><option key={p.id} value={p.id}>{p.title||p.input_text||p.id}</option>)}</select></label>
   <label>Workspace<select required className="block w-full bg-slate-900 p-2" value={workspace} onChange={e=>setWorkspace(e.target.value)}><option value="">Choose owned workspace</option>{workspaces.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select></label>
   <label>Contributor<select required className="block w-full bg-slate-900 p-2" value={member} onChange={e=>setMember(e.target.value)}><option value="">Choose member</option>{members.map(m=><option key={m.user_id} value={m.user_id}>{m.display_name||m.email||m.user_id}</option>)}</select></label>
   <label>Discipline<select className="block w-full bg-slate-900 p-2" value={kind} onChange={e=>setKind(e.target.value)}>{discipline.map(d=><option key={d}>{d}</option>)}</select></label>
   <label>Task title<input required minLength={3} maxLength={180} className="block w-full bg-slate-900 p-2" value={title} onChange={e=>setTitle(e.target.value)}/></label>
   <button disabled={busy||!member||!project||!title.trim()} className="rounded bg-emerald-300 text-slate-950 p-2 disabled:opacity-40">Assign task</button></form>}
   <h3 className="font-semibold">Assigned work</h3>
   {!tasks.length&&<p className="text-slate-400">No accessible assignments.</p>}
   {tasks.map(t=>{const owner=t.assigned_by===user?.userId;const next=owner?(t.status==="submitted"?["completed","in_progress"]:t.status==="completed"?["in_progress"]:[]):(t.status==="assigned"?["in_progress"]:t.status==="in_progress"?["submitted"]:[]);return <div key={t.id} className="border border-white/10 rounded p-3 space-y-2"><p className="font-semibold">{t.title}</p><p>{t.project_title} · {t.discipline} · {t.status.replaceAll("_"," ")}</p><div className="flex gap-3 flex-wrap">{t.can_update&&next.map(status=><button key={status} type="button" disabled={busy} className="underline" onClick={()=>void mutate("/assignments/"+t.id,"PATCH",{expected_status:t.status,status})}>{status.replaceAll("_"," ")}</button>)}{owner&&<button type="button" disabled={busy} className="underline text-red-300" onClick={()=>{if(window.confirm("Revoke this assignment?"))void mutate("/assignments/"+t.id,"DELETE");}}>Revoke</button>}</div></div>;})}
   <div className="flex gap-3"><button disabled={!offset||busy} onClick={()=>void load(Math.max(0,offset-50)).catch(e=>setError(e.message))}>Previous</button><button disabled={tasks.length<50||busy} onClick={()=>void load(offset+50).catch(e=>setError(e.message))}>Next</button></div></>}
 </section>;
}
