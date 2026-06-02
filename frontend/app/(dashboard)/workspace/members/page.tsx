"use client";
import { Users } from "lucide-react";
import { useState } from "react";

// TODO: Wire to real API when Yehor's endpoint is ready
// Expected: GET /api/v1/workspace/members?workspace_id=...
// Expected response shape: [{ id, name, email, role, avatar_url, joined_at }]

export default function MembersPage() {
    const [isLoading] = useState(false);
    const [members] = useState<unknown[]>([]);

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Members</h1>
                <p className="text-[#8F8F8F]">Manage who has access to your workspace.</p>

                {/* Loading skeleton */}
                {isLoading && (
                    <div className="flex flex-col gap-3 mt-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4">
                                <div className="skeleton h-12 w-12 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-1/3 rounded-md" />
                                    <div className="skeleton h-3 w-1/2 rounded-sm" />
                                </div>
                                <div className="skeleton h-8 w-20 rounded-lg" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && members.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl mt-4">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Users className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No members yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Invite team members to collaborate on your workspace.
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
