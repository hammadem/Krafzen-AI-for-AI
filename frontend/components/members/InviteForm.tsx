"use client";

// Invite a new member. Handles inline validation + a "sending" state.
// Duplicate handling is enforced by the parent (and the backend) — this just
// surfaces the resulting message.

import { useState } from "react";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { UserPlus, Loader2 } from "lucide-react";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function InviteForm({
    onInvite,
}: {
    /** Returns true on success (form clears), false to keep the entered values. */
    onInvite: (email: string, role: string) => Promise<boolean>;
}) {
    const [email, setEmail] = useState("");
    const [role, setRole] = useState<string>("member");
    const [sending, setSending] = useState(false);
    const [localError, setLocalError] = useState<string | null>(null);

    const submit = async () => {
        const trimmed = email.trim();
        if (!EMAIL_RE.test(trimmed)) {
            setLocalError("Enter a valid email address.");
            return;
        }
        setLocalError(null);
        setSending(true);
        const ok = await onInvite(trimmed, role);
        setSending(false);
        if (ok) {
            setEmail("");
            setRole("member");
        }
    };

    return (
        <div className="bg-[#2F2F2F] rounded-[10px] p-4 flex flex-col gap-3">
            <h3 className="text-white font-medium">Invite a member</h3>
            <div className="flex flex-col sm:flex-row gap-3">
                <Input
                    type="email"
                    value={email}
                    onChange={(e) => {
                        setEmail(e.target.value);
                        if (localError) setLocalError(null);
                    }}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !sending) submit();
                    }}
                    placeholder="teammate@email.com"
                    disabled={sending}
                    className="bg-[#1f1f1f] border-white/10 text-sm flex-1"
                />
                <Select value={role} onValueChange={setRole} disabled={sending}>
                    <SelectTrigger className="w-full sm:w-[140px] border-white/10 bg-[#1f1f1f]">
                        <SelectValue placeholder="Role" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="member">Member</SelectItem>
                            <SelectItem value="viewer">Viewer</SelectItem>
                        </SelectGroup>
                    </SelectContent>
                </Select>
                <button
                    onClick={submit}
                    disabled={sending}
                    className="flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-[#54e3b5] text-black text-sm font-medium hover:bg-[#46d0a4] transition-colors disabled:opacity-60 disabled:cursor-not-allowed shrink-0"
                >
                    {sending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <UserPlus className="w-4 h-4" />
                    )}
                    {sending ? "Sending…" : "Send invite"}
                </button>
            </div>
            {localError && <p className="text-red-400 text-xs">{localError}</p>}
        </div>
    );
}
