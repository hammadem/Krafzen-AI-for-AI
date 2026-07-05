"use client";

// Pending invitations list with a confirm-to-revoke flow.
// Revoke is optimistic in the parent, so a confirmed row disappears instantly.

import { Mail, X } from "lucide-react";
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

function expiryLabel(iso: string): string {
    const ms = new Date(iso).getTime() - Date.now();
    if (Number.isNaN(ms)) return "";
    const days = Math.ceil(ms / (1000 * 60 * 60 * 24));
    if (days <= 0) return "Expired";
    if (days === 1) return "Expires in 1 day";
    return `Expires in ${days} days`;
}

export default function PendingInvites({
    invites,
    onRevoke,
}: {
    invites: WorkspaceInvite[];
    onRevoke: (inviteId: string) => void;
}) {
    if (invites.length === 0) return null;

    return (
        <div className="flex flex-col gap-2">
            <h3 className="text-[#8F8F8F] text-xs uppercase tracking-wide">
                Pending invitations ({invites.length})
            </h3>
            <div className="flex flex-col gap-2">
                {invites.map((inv) => (
                    <div
                        key={inv.id}
                        className="bg-[#2F2F2F] rounded-[10px] p-3 flex items-center gap-3"
                    >
                        <div className="w-9 h-9 rounded-full bg-yellow-400/10 border border-yellow-400/20 flex items-center justify-center shrink-0">
                            <Mail className="w-4 h-4 text-yellow-400/80" />
                        </div>
                        <div className="flex flex-col flex-1 min-w-0">
                            <span className="text-white text-sm truncate">{inv.email}</span>
                            <span className="text-[#8F8F8F] text-xs">
                                <span className="capitalize">{inv.role}</span>
                                {inv.expires_at ? ` · ${expiryLabel(inv.expires_at)}` : ""}
                            </span>
                        </div>
                        <span className="px-2.5 py-1 rounded-lg text-xs border bg-yellow-400/10 text-yellow-400 border-yellow-400/20 shrink-0">
                            Pending
                        </span>

                        <AlertDialog>
                            <AlertDialogTrigger asChild>
                                <button
                                    aria-label="Revoke invite"
                                    className="p-2 text-[#94a3b8] hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors shrink-0"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </AlertDialogTrigger>
                            <AlertDialogContent className="bg-[#1f1f1f] border-white/10">
                                <AlertDialogHeader>
                                    <AlertDialogTitle className="text-white">
                                        Revoke this invitation?
                                    </AlertDialogTitle>
                                    <AlertDialogDescription className="text-[#94a3b8]">
                                        The invite to <span className="text-white">{inv.email}</span> will
                                        no longer be valid. You can always send a new one.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                    <AlertDialogCancel className="bg-transparent border-white/10 text-white hover:bg-white/5">
                                        Cancel
                                    </AlertDialogCancel>
                                    <AlertDialogAction
                                        onClick={() => onRevoke(inv.id)}
                                        className="bg-red-500/90 text-white hover:bg-red-500"
                                    >
                                        Revoke
                                    </AlertDialogAction>
                                </AlertDialogFooter>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>
                ))}
            </div>
        </div>
    );
}
