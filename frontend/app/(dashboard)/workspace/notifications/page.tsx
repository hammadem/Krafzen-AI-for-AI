"use client";
import { Bell, RefreshCw, AlertCircle } from "lucide-react";
import { useState, useEffect } from "react";
import { getDashboardNotifications, markNotificationRead } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";
import { apiCache } from "@/lib/api/cache";

// Wired to Tazwar's endpoint (dashboard_routes.py)
// GET /api/v1/dashboard/notifications  (auth-scoped; supports ?unread_only=true & ?limit=N)
// Response shape: { notifications: [{ id, title, message, read, created_at, type }], total }

interface NotificationItem {
    id: string;
    title: string;
    message: string;
    read: boolean;
    created_at: string;
    type: string;
}

export default function NotificationsPage() {
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [notifications, setNotifications] = useState<NotificationItem[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        if (!user?.userId) return;
        let isMounted = true;

        const load = async () => {
            setIsLoading(true);
            setError(null);

            const { ok, data, error: apiError } = await getDashboardNotifications(user);
            if (!isMounted) return;

            if (ok && data && typeof data === "object" && "notifications" in data) {
                const list = (data as { notifications?: NotificationItem[] }).notifications;
                setNotifications(Array.isArray(list) ? list : []);
            } else if (ok) {
                setNotifications([]);
            } else {
                setError(apiError?.message || "Could not load notifications.");
            }

            setIsLoading(false);
        };

        load();
        return () => {
            isMounted = false;
        };
    }, [user, reloadKey]);

    const handleMarkRead = async (id: string) => {
        const target = notifications.find((n) => n.id === id);
        if (!target || target.read) return;

        // Optimistic update
        setNotifications((prev) =>
            prev.map((n) => (n.id === id ? { ...n, read: true } : n))
        );

        const { ok } = await markNotificationRead(user, id);
        if (ok) {
            // Keep cache fresh for next mount
            apiCache.delete(`GET:/api/v1/dashboard/notifications`);
        } else {
            // Rollback on failure
            setNotifications((prev) =>
                prev.map((n) => (n.id === id ? { ...n, read: false } : n))
            );
        }
    };

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Notifications</h1>
                <p className="text-[#8F8F8F]">Stay updated on your project generations and account activity.</p>

                {/* Error state */}
                {error && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Failed to load notifications</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">{error}</p>
                        </div>
                        <button
                            onClick={() => setReloadKey((k) => k + 1)}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try again
                        </button>
                    </div>
                )}

                {/* Loading skeleton */}
                {isLoading && !error && (
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

                {/* Notifications list */}
                {!isLoading && !error && notifications.length > 0 && (
                    <div className="flex flex-col gap-3 mt-4">
                        {notifications.map((n) => (
                            <button
                                key={n.id}
                                onClick={() => handleMarkRead(n.id)}
                                className={`text-left rounded-[10px] p-4 flex items-start gap-4 transition-all border ${
                                    n.read
                                        ? "bg-[#2F2F2F] border-transparent"
                                        : "bg-[#54e3b5]/5 border-[#54e3b5]/20 hover:bg-[#54e3b5]/10"
                                }`}
                            >
                                <div className="w-10 h-10 rounded-full bg-[#54e3b5]/10 flex items-center justify-center shrink-0 border border-[#54e3b5]/20 relative">
                                    <Bell className="w-5 h-5 text-[#54e3b5]/70" />
                                    {!n.read && (
                                        <span className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-[#54e3b5] rounded-full border-2 border-[#191919]" />
                                    )}
                                </div>
                                <div className="flex flex-col gap-1 flex-1">
                                    <p className={`text-sm ${n.read ? "text-[#cfcfcf] font-normal" : "text-white font-semibold"}`}>
                                        {n.title}
                                    </p>
                                    <p className="text-[#94a3b8] text-sm">{n.message}</p>
                                    <span className="text-[#8F8F8F] text-xs capitalize">
                                        {n.type}
                                        {n.created_at ? ` · ${new Date(n.created_at).toLocaleString()}` : ""}
                                    </span>
                                </div>
                            </button>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !error && notifications.length === 0 && (
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
