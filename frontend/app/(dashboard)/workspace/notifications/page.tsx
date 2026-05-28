"use client";
import { Bell } from "lucide-react";
import { useState } from "react";

// TODO: Wire to real API when Yehor's endpoint is ready
// Expected: GET /api/v1/notifications?user_id=...
// Expected response shape: [{ id, title, message, read, created_at, type }]

export default function NotificationsPage() {
    const [isLoading, setIsLoading] = useState(false);
    const [notifications] = useState<unknown[]>([]);

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Notifications</h1>
                <p className="text-[#8F8F8F]">Stay updated on your project generations and account activity.</p>

                {/* Loading skeleton */}
                {isLoading && (
                    <div className="flex flex-col gap-3 mt-4">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-start gap-4">
                                <div className="skeleton h-10 w-10 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-1/2 rounded-md" />
                                    <div className="skeleton h-3 w-3/4 rounded-sm" />
                                    <div className="skeleton h-3 w-1/4 rounded-sm" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && notifications.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl mt-4">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Bell className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No notifications yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                You&apos;ll be notified when your CAD files are ready or your plan changes.
            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
