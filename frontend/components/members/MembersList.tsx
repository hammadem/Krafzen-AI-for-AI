"use client";

// Workspace members with inline role changes + confirm-to-remove.
// Both actions are optimistic in the parent. The current user and the workspace
// owner are protected (can't be demoted or removed here).

import { Trash2 } from "lucide-react";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

function labelFor(m: WorkspaceMember): string {
    return m.display_name || m.email || m.user_id;
}

export default function MembersList({
    members,
    currentUserId,
    onRoleChange,
    onRemove,
}: {
    members: WorkspaceMember[];
    currentUserId?: string;
    onRoleChange: (userId: string, role: string) => void;
    onRemove: (userId: string) => void;
}) {
    return (
        <div className="flex flex-col gap-3">
            {members.map((m) => {
                const isSelf = m.user_id === currentUserId;
                const isOwner = m.role?.toLowerCase() === "owner";
                const locked = isSelf || isOwner; // protect self + owner
                const name = labelFor(m);

                return (
                    <div
                        key={m.user_id}
                        className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4"
                    >
                        <div className="h-11 w-11 rounded-full bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center shrink-0 text-[#54e3b5] font-semibold uppercase">
                            {(name || "?").charAt(0)}
                        </div>
                        <div className="flex flex-col flex-1 min-w-0">
                            <span className="text-white font-medium truncate">
                                {name}
                                {isSelf && <span className="text-[#8F8F8F] font-normal"> (you)</span>}
                            </span>
                            {m.email && m.email !== name && (
                                <span className="text-[#94a3b8] text-sm truncate">{m.email}</span>
                            )}
                        </div>

                        {/* Role: editable, or a static badge when locked */}
                        {locked ? (
                            <span className="px-3 py-1 rounded-lg bg-[#54e3b5]/10 border border-[#54e3b5]/20 text-[#54e3b5] text-xs capitalize shrink-0">
                                {m.role}
                            </span>
                        ) : (
                            <Select value={m.role} onValueChange={(role) => onRoleChange(m.user_id, role)}>
                                <SelectTrigger className="w-[120px] border-white/10 bg-[#1f1f1f] h-9 text-xs capitalize">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectGroup>
                                        <SelectItem value="admin">Admin</SelectItem>
                                        <SelectItem value="member">Member</SelectItem>
                                        <SelectItem value="viewer">Viewer</SelectItem>
                                    </SelectGroup>
                                </SelectContent>
                            </Select>
                        )}

                        {/* Remove (confirm) — hidden for self + owner */}
                        {!locked && (
                            <AlertDialog>
                                <AlertDialogTrigger asChild>
                                    <button
                                        aria-label={`Remove ${name}`}
                                        className="p-2 text-[#94a3b8] hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors shrink-0"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </AlertDialogTrigger>
                                <AlertDialogContent className="bg-[#1f1f1f] border-white/10">
                                    <AlertDialogHeader>
                                        <AlertDialogTitle className="text-white">
                                            Remove {name}?
                                        </AlertDialogTitle>
                                        <AlertDialogDescription className="text-[#94a3b8]">
                                            They&apos;ll lose access to this workspace immediately. You can
                                            invite them again later.
                                        </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                        <AlertDialogCancel className="bg-transparent border-white/10 text-white hover:bg-white/5">
                                            Cancel
                                        </AlertDialogCancel>
                                        <AlertDialogAction
                                            onClick={() => onRemove(m.user_id)}
                                            className="bg-red-500/90 text-white hover:bg-red-500"
                                        >
                                            Remove
                                        </AlertDialogAction>
                                    </AlertDialogFooter>
                                </AlertDialogContent>
                            </AlertDialog>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
