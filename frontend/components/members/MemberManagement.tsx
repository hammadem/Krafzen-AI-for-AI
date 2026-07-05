"use client";

// Orchestrates Step 3: members + invites for one workspace.
// Owns the optimistic update logic; the child components are presentational.

import { useCallback } from "react";
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

export default function MemberManagement({ workspaceId }: { workspaceId: string }) {
    const { user } = useAuth();

    const {
        data: members,
        setData: setMembers,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<WorkspaceMember[]>({
        fetcher: (u) => getWorkspaceMembers(u, workspaceId),
        select: selectMembers,
        fallback: [],
        enabled: !!workspaceId,
    });

    const { data: invites, setData: setInvites } = useApiResource<WorkspaceInvite[]>({
        fetcher: (u) => getWorkspaceInvites(u, workspaceId),
        select: selectInvites,
        fallback: [],
        enabled: !!workspaceId,
    });

    const pendingInvites = invites.filter((i) => i.status === "pending");

    // --- Invite (with client + server duplicate handling) ---
    const handleInvite = useCallback(
        async (email: string, role: string): Promise<boolean> => {
            const dupe = invites.some(
                (i) => i.status === "pending" && i.email.toLowerCase() === email.toLowerCase()
            );
            if (dupe) {
                toast.dark("An invite is already pending for that email.");
                return false;
            }
            const { ok, data, error: apiError } = await createInvite(user, workspaceId, { email, role });
            if (ok && data) {
                setInvites((prev) => [data as unknown as WorkspaceInvite, ...prev]);
                toast.dark(`Invite sent to ${email}`);
                return true;
            }
            toast.dark(apiError?.message || "Could not send the invite.");
            return false;
        },
        [invites, user, workspaceId, setInvites]
    );

    // --- Revoke invite (optimistic) ---
    const handleRevoke = useCallback(
        async (inviteId: string) => {
            let prevStatus: WorkspaceInvite["status"] | undefined;
            setInvites((prev) =>
                prev.map((i) => {
                    if (i.id === inviteId) {
                        prevStatus = i.status;
                        return { ...i, status: "revoked" };
                    }
                    return i;
                })
            );
            const { ok } = await revokeInvite(user, workspaceId, inviteId);
            if (!ok && prevStatus) {
                setInvites((prev) =>
                    prev.map((i) => (i.id === inviteId ? { ...i, status: prevStatus! } : i))
                );
                toast.dark("Couldn't revoke the invite. Please try again.");
            }
        },
        [user, workspaceId, setInvites]
    );

    // --- Change role (optimistic) ---
    const handleRoleChange = useCallback(
        async (userId: string, role: string) => {
            let prevRole: string | undefined;
            setMembers((prev) =>
                prev.map((m) => {
                    if (m.user_id === userId) {
                        prevRole = m.role;
                        return { ...m, role };
                    }
                    return m;
                })
            );
            const { ok } = await updateMemberRole(user, workspaceId, userId, role);
            if (!ok && prevRole !== undefined) {
                setMembers((prev) =>
                    prev.map((m) => (m.user_id === userId ? { ...m, role: prevRole! } : m))
                );
                toast.dark("Couldn't update the role. Please try again.");
            }
        },
        [user, workspaceId, setMembers]
    );

    // --- Remove member (optimistic, with re-insert rollback) ---
    const handleRemove = useCallback(
        async (userId: string) => {
            let removed: WorkspaceMember | undefined;
            let index = -1;
            setMembers((prev) => {
                index = prev.findIndex((m) => m.user_id === userId);
                removed = prev[index];
                return prev.filter((m) => m.user_id !== userId);
            });
            const { ok } = await removeWorkspaceMember(user, workspaceId, userId);
            if (!ok && removed) {
                setMembers((prev) => {
                    const copy = [...prev];
                    copy.splice(index < 0 ? copy.length : index, 0, removed!);
                    return copy;
                });
                toast.dark("Couldn't remove the member. Please try again.");
            }
        },
        [user, workspaceId, setMembers]
    );

    return (
        <div className="flex flex-col gap-5">
            <InviteForm onInvite={handleInvite} />

            <PendingInvites invites={pendingInvites} onRevoke={handleRevoke} />

            {/* Members */}
            <div className="flex flex-col gap-2">
                <h3 className="text-[#8F8F8F] text-xs uppercase tracking-wide">
                    Members{!isLoading && !isError ? ` (${members.length})` : ""}
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
                        onRoleChange={handleRoleChange}
                        onRemove={handleRemove}
                    />
                )}

                {!isLoading && !isError && members.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-12 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-14 h-14 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Users className="w-6 h-6 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold">No members yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Invite teammates above to collaborate on your workspace.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
