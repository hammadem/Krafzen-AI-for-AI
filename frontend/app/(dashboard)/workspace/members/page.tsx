"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { listWorkspaces, createWorkspace, acceptWorkspaceInvite, declineWorkspaceInvite } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import MemberManagement from "@/components/members/MemberManagement";

type OwnedWorkspaceInfo = WorkspaceInfo & { owner_id: string };

export default function MembersPage() {
    const {user} = useAuth();
    const {data: workspaces, isLoading, isError, error, refetch} = useApiResource<OwnedWorkspaceInfo[]>({
        fetcher: u => listWorkspaces(u),
        select: raw => Array.isArray(raw) ? raw as unknown as OwnedWorkspaceInfo[] : [],
        fallback: [],
    });
    const [selectedId, setSelectedId] = useState("");
    const [name, setName] = useState("");
    const [inviteCode, setInviteCode] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [actionError, setActionError] = useState("");
    const workspace = workspaces.find(w => w.id === selectedId) || workspaces[0];
    const canManage = !!workspace && workspace.owner_id === user?.userId;
    const mutate = async (action: "create" | "accept" | "decline") => {
        if (busy || !user) return;
        if (action === "decline" && !window.confirm("Decline this invitation? You will need a new code to join later.")) return;
        setBusy(true); setMessage(""); setActionError("");
        try {
            const result = action === "create" ? await createWorkspace(user, name.trim()) : action === "accept" ? await acceptWorkspaceInvite(user, inviteCode.trim()) : await declineWorkspaceInvite(user, inviteCode.trim());
            if (!result.ok) { setActionError(result.error?.message || "Workspace action failed."); return; }
            const raw = result.data as unknown as {id?:string;workspace_id?:string};
            if (action !== "decline") setSelectedId(raw?.id || raw?.workspace_id || "");
            setName(""); setInviteCode("");
            setMessage(action === "create" ? "Workspace created." : action === "accept" ? "Invitation accepted." : "Invitation declined.");
            refetch();
        } catch { setActionError("Workspace service unavailable. Try again."); }
        finally { setBusy(false); }
    };
    return <div className="flex flex-col gap-6 p-5 text-white overflow-y-auto">
        <h1 className="text-2xl font-semibold">Members</h1>
        <p className="text-sm text-slate-400">Create a team, accept or decline an invitation, or manage a workspace you own. Project sharing is subject to its separate access controls.</p>
        {message && <p role="status" className="text-emerald-300">{message}</p>}
        {actionError && <p role="alert" className="text-red-300">{actionError}</p>}
        <div className="grid gap-4 md:grid-cols-2">
            <form className="flex flex-col gap-2 rounded-xl border border-white/10 p-4" onSubmit={e=>{e.preventDefault();void mutate("create");}}>
                <label htmlFor="workspace-name">New workspace name</label>
                <input id="workspace-name" className="bg-black border border-white/20 rounded p-2" required maxLength={120} value={name} onChange={e=>setName(e.target.value)}/>
                <button className="bg-emerald-400 text-black rounded p-2 font-semibold" disabled={busy || !name.trim()}>Create workspace</button>
            </form>
            <form className="flex flex-col gap-2 rounded-xl border border-white/10 p-4" onSubmit={e=>{e.preventDefault();void mutate("accept");}}>
                <label htmlFor="invite-code">Invitation code</label>
                <input id="invite-code" className="bg-black border border-white/20 rounded p-2" required maxLength={36} value={inviteCode} onChange={e=>setInviteCode(e.target.value)}/>
                <button className="bg-white/10 rounded p-2 font-semibold" disabled={busy || !inviteCode.trim()}>Accept invitation</button>
                <button type="button" className="border border-white/20 rounded p-2 font-semibold disabled:opacity-40" disabled={busy || !inviteCode.trim()} onClick={()=>void mutate("decline")}>Decline invitation</button>
            </form>
        </div>
        {isLoading && <p role="status">Loading workspaces…</p>}
        {isError && <div><p role="alert">{error?.message || "Could not load workspaces."}</p><button className="underline" onClick={refetch}>Retry</button></div>}
        {!isLoading && !isError && workspace && <>
            <label htmlFor="workspace-select">Current workspace</label>
            <select id="workspace-select" value={workspace.id} onChange={e=>setSelectedId(e.target.value)} className="bg-black border border-white/20 rounded p-2">
                {workspaces.map(w=><option key={w.id} value={w.id}>{w.name}{w.owner_id===user?.userId ? " (owner)" : ""}</option>)}
            </select>
            <p className="text-sm text-slate-400">{canManage ? "You own this workspace." : "Only the owner can invite, remove members, and modify roles."}</p>
            <MemberManagement key={workspace.id} workspaceId={workspace.id} canManage={canManage}/>
        </>}
        {!isLoading && !isError && !workspace && <p className="text-slate-400">No team workspace yet. Create one or accept an invitation.</p>}
    </div>;
}
