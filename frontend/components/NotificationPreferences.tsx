"use client";
import {useEffect,useState} from "react";
import {getApiBaseUrl} from "@/lib/api/utils";
const categories={imports:"Imports",exports:"Export results",reviews:"Drawing reviews and review-required exports",field:"Field observations",collaboration:"Project assignments and collaboration",validation:"BIM and compliance validation"};
type Preferences=Record<keyof typeof categories,boolean>;
export default function NotificationPreferences({user,onReadAll}:{user:User|null;onReadAll:()=>void}){
 const [open,setOpen]=useState(false),[prefs,setPrefs]=useState<Preferences|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(""),[notice,setNotice]=useState("");
 const request=async(path:string,method:string,body?:Preferences)=>{
   if(!user?.access_token)throw Error("Sign in required");
   const r=await fetch(getApiBaseUrl().replace(/\/$/,"")+"/api/v1/notifications/"+path,{method,headers:{Authorization:"Bearer "+user.access_token,"Content-Type":"application/json",apikey:process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY||""},...(body?{body:JSON.stringify(body)}:{})});
   const data=await r.json().catch(()=>({}));if(!r.ok)throw Error(typeof data.detail==="string"?data.detail:"Notification request failed");return data;
 };
 useEffect(()=>{if(!open||!user?.access_token)return;let active=true;setPrefs(null);setError("");request("preferences","GET").then(data=>{if(active)setPrefs(data);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[open,user?.access_token]);
 const save=async()=>{if(!prefs||busy)return;setBusy(true);setError("");setNotice("");try{setPrefs(await request("preferences","PUT",prefs));setNotice("Preferences saved.");}catch(e){setError(e instanceof Error?e.message:"Save failed");}finally{setBusy(false);}};
 const readAll=async()=>{if(busy)return;setBusy(true);setError("");try{await request("read-all","POST");onReadAll();}catch(e){setError(e instanceof Error?e.message:"Update failed");}finally{setBusy(false);}};
 return <div className="rounded-xl border border-white/10 p-3 space-y-3 text-sm">
 <div className="flex gap-4"><button className="underline" type="button" onClick={()=>setOpen(v=>!v)}>{open?"Hide preferences":"Notification preferences"}</button><button type="button" className="underline" disabled={busy||!user} onClick={()=>void readAll()}>Mark all as read</button></div>
 {open&&<><p className="text-slate-400">Choose future in-app notifications. Existing history is preserved. Email delivery is not configured here.</p>{prefs?(Object.keys(categories) as Array<keyof Preferences>).map(key=><label key={key} className="flex items-center gap-2"><input type="checkbox" disabled={busy} checked={prefs[key]} onChange={e=>setPrefs({...prefs,[key]:e.target.checked})}/>{categories[key]}</label>):!error&&<p role="status">Loading preferences…</p>}<button disabled={!prefs||busy} type="button" onClick={()=>void save()} className="rounded bg-emerald-300 px-3 py-2 text-slate-950 disabled:opacity-40">Save preferences</button></>}
 {notice&&<p role="status">{notice}</p>}{error&&<p role="alert" className="text-red-300">{error}</p>}</div>;
}
