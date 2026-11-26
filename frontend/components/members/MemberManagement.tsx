"use client";

// Orchestrates Step 3: members + invites for one workspace.
// Reloads authoritative server state after member mutations.

import { useCallback, useRef, useState } from "react";
import { Users, RefreshCw, AlertCircle } from "lucide-react";
import { toast } from "react-toastify";
import { useAuth } from "@/context/AuthContext";
import { useApiResource } from "@/hooks/useApiResource";
import {
    getWorkspaceMembers,
    getWorkspaceInvites,
    updateMemberRole,
    removeWorkspaceMember,
    createInvite,
    revokeInvite,
} from "@/lib/api/api";
import InviteForm from "@/components/members/InviteForm";
import PendingInvites from "@/components/members/PendingInvites";
import MembersList from "@/components/members/MembersList";

function selectMembers(raw: ApiRes["data"]): WorkspaceMember[] {
    if (raw && typeof raw === "object" && "members" in raw) {
        const list = (raw as { members?: WorkspaceMember[] }).members;
        return Array.isArray(list) ? list : [];
    }
    return Array.isArray(raw) ? (raw as unknown as WorkspaceMember[]) : [];
}

function selectInvites(raw: ApiRes["data"]): WorkspaceInvite[] {
    if (Array.isArray(raw)) return raw as unknown as WorkspaceInvite[];
    if (raw && typeof raw === "object" && "invites" in raw) {
        const list = (raw as { invites?: WorkspaceInvite[] }).invites;
        return Array.isArray(list) ? list : [];
    }
    return [];
}

export default function MemberManagement({ workspaceId, canManage = true }: { workspaceId: string; canManage?: boolean }) {
    const { user } = useAuth();
    const [page, setPage] = useState(1);
    const [changing, setChanging] = useState(false);
    const mutationLock = useRef(false);

    const {
        data: memberPage,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<{ members: WorkspaceMember[]; total: number }>({
        fetcher: (u) => getWorkspaceMembers(u, workspaceId, page, 50),
        select: raw => ({ members: selectMembers(raw), total: Number((raw as { total?: number })?.total ?? selectMembers(raw).length) }),
        fallback: { members: [], total: 0 },
        enabled: !!workspaceId,
        resourceKey: `${workspaceId}:${page}`,
    });
    const members = memberPage.members;

    const { data: invites, setData: setInvites, isError: invitesError, error: inviteError, refetch: refetchInvites } = useApiResource<WorkspaceInvite[]>({
        fetcher: (u) => getWorkspaceInvites(u, workspaceId),
        select: selectInvites,
        fallback: [],
        enabled: !!workspaceId && canManage,
        resourceKey: workspaceId,
    });

    const pendingInvites = invites.filter((i) => i.status === "pending" && new Date(i.expires_at).getTime() > Date.now());

    // --- Invite (with client + server duplicate handling) ---
    const handleInvite = useCallback(
        async (email: string, role: string): Promise<boolean> => {
            const dupe = invites.some(
                (i) => i.status === "pending" && new Date(i.expires_at).getTime() > Date.now() && i.email.toLowerCase() === email.toLowerCase()
            );
            if (dupe) {
                toast.dark("An invite is already pending for that email.");
                return false;
            }
            const { ok, data, error: apiError } = await createInvite(user, workspaceId, { email, role });
            if (ok && data) {
                const invite = data as unknown as WorkspaceInvite;
                setInvites((prev) => [invite, ...prev.filter(i => i.id !== invite.id)]);
                toast.dark("Invitation created. Copy the code and share it privately.");
                return true;
            }
            toast.dark(apiError?.message || "Could not send the invite.");
            return false;
        },
        [invites, user, workspaceId, setInvites]
    );

    // Serialize mutations; re-read authoritative data after success or failure.
    const change = useCallback(async (operation: () => Promise<ApiRes>, refresh: () => void, fallback: string) => {
        if (mutationLock.current) return;
        mutationLock.current = true;
        setChanging(true);
        try {
            const result = await operation();
            if (!result.ok) toast.dark(result.error?.message || fallback);
        } catch {
            toast.dark(fallback);
        } finally {
            refresh();
            mutationLock.current = false;
            setChanging(false);
        }
    }, []);

    const handleRevoke = (id: string) => change(() => revokeInvite(user, workspaceId, id), refetchInvites, "Could not revoke invitation.");
    const handleRoleChange = (id: string, role: string) => change(() => updateMemberRole(user, workspaceId, id, role), refetch, "Could not update role.");
    const handleRemove = (id: string) => change(() => removeWorkspaceMember(user, workspaceId, id), refetch, "Could not remove member.");

    return (
        <div className="flex flex-col gap-5">
            {canManage && <><InviteForm onInvite={handleInvite} />
            <p className="text-xs text-slate-400">Invitations are not emailed automatically. Share the code privately with the intended email account.</p>
            {invitesError && <p role="alert">{inviteError?.message || "Could not load invitations."} <button onClick={refetchInvites} className="underline">Retry</button></p>}
            <fieldset disabled={changing}><PendingInvites invites={pendingInvites} onRevoke={handleRevoke} /></fieldset>
            {!!invites.filter(i=>!pendingInvites.includes(i)).length && <details className="rounded-lg border border-white/10 p-3"><summary className="cursor-pointer text-sm">Invitation history</summary>{invites.filter(i=>!pendingInvites.includes(i)).map(i=><div key={i.id} className="flex flex-wrap justify-between gap-2 py-2 text-xs border-b border-white/10"><span>{i.email} · {i.role}</span><span>{i.status === "revoked" ? "Invalidated — revoked or declined" : i.status === "pending" ? "Expired" : i.status}</span></div>)}<p className="text-xs text-slate-400">The activity timeline records who revoked or declined an invitation.</p></details>}</>}

            {/* Members */}
            <div className="flex flex-col gap-2">
                <h3 className="text-[#8F8F8F] text-xs uppercase tracking-wide">
                    Members{!isLoading && !isError ? ` (${memberPage.total})` : ""}
                </h3>

                {isError && (
                    <div className="flex flex-col items-center justify-center py-12 gap-4">
                        <div className="w-14 h-14 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-7 h-7 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Failed to load members</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                {error?.message || "Could not load members."}
                            </p>
                        </div>
                        <button
                            onClick={refetch}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try again
                        </button>
                    </div>
                )}

                {isLoading && !isError && (
                    <div className="flex flex-col gap-3">
                        {[1, 2, 3].map((i) => (
                            <div
                                key={i}
                                className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4"
                            >
                                <div className="skeleton h-11 w-11 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-1/3 rounded-md" />
                                    <div className="skeleton h-3 w-1/2 rounded-sm" />
                                </div>
                                <div className="skeleton h-9 w-24 rounded-lg" />
                            </div>
                        ))}
                    </div>
                )}

                {!isLoading && !isError && members.length > 0 && (
                    <MembersList
                        members={members}
                        currentUserId={user?.userId}
                        canManage={canManage && !changing}
                        onRoleChange={handleRoleChange}
                        onRemove={handleRemove}
                    />
                )}

                {!isLoading && !isError && (page > 1 || memberPage.total > 50) && <nav aria-label="Member pagination" className="flex items-center gap-3">
                    <button disabled={page === 1 || changing} onClick={() => setPage(p => p - 1)} className="rounded border border-white/20 px-3 py-1 disabled:opacity-40">Previous</button>
                    <span>Page {page} of {Math.max(1, Math.ceil(memberPage.total / 50))}</span>
                    <button disabled={page * 50 >= memberPage.total || changing} onClick={() => setPage(p => p + 1)} className="rounded border border-white/20 px-3 py-1 disabled:opacity-40">Next</button>
                </nav>}
                {!isLoading && !isError && members.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-14 h-14 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Users className="w-6 h-6 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold">No members yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                {canManage ? "Create an invitation to add a teammate." : "No additional members in this workspace."}
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
