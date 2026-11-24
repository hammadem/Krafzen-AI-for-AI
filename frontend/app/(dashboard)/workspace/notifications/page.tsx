"use client";
import { Bell, RefreshCw, AlertCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getDashboardNotifications, markNotificationRead } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";
import NotificationPreferences from "@/components/NotificationPreferences";
import { useApiResource } from "@/hooks/useApiResource";

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

const PAGE_SIZE = 20;
type NotificationPage = { notifications: NotificationItem[]; total: number };

export default function NotificationsPage() {
    const { user } = useAuth();
    return <NotificationInbox key={user?.userId || "signed-out"} />;
}

function NotificationInbox() {
    const { user } = useAuth();
    const [offset, setOffset] = useState(0);
    const [unreadOnly, setUnreadOnly] = useState(false);
    const [markError, setMarkError] = useState<string | null>(null);
    const [pending, setPending] = useState<string | null>(null);
    const active = useRef(true);
    useEffect(() => { active.current = true; return () => { active.current = false; }; }, []);
    const {
        data, isLoading, isError, error, refetch,
    } = useApiResource<NotificationPage>({
        fetcher: (u) => getDashboardNotifications(u, { limit: PAGE_SIZE, offset, unreadOnly }),
        select: (raw) => raw as unknown as NotificationPage,
        fallback: { notifications: [], total: 0 },
    });
    const notifications = data.notifications;

    const handleMarkRead = async (id: string) => {
        const target = notifications.find((n) => n.id === id);
        if (!target || target.read || pending) return;
        setPending(id);
        setMarkError(null);
        try {
            const result = await markNotificationRead(user, id);
            if (!result.ok) throw new Error(result.error?.message || "Could not mark notification as read.");
            if (active.current) {
                if (unreadOnly && notifications.length === 1 && offset > 0) setOffset(Math.max(0, offset - PAGE_SIZE));
                refetch();
            }
        } catch (cause) {
            if (active.current) setMarkError(cause instanceof Error ? cause.message : "Could not mark notification as read.");
        } finally {
            if (active.current) setPending(null);
        }
    };

    const changePage = (next: number) => {
        setOffset(next);
        setMarkError(null);
        refetch();
    };

    return (
        <div className="text-white flex p-4 flex-col items-stretch sm:items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-full sm:w-[80%] p-2 sm:p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-2xl sm:text-[4vh]">Notifications</h1>
                <p className="text-[#8F8F8F]">Stay updated on saved project notifications.</p>
                <div className="flex flex-wrap items-center gap-4 text-sm">
                    <label className="flex items-center gap-2"><input type="checkbox" checked={unreadOnly} disabled={isLoading || !!pending} onChange={(e) => { setUnreadOnly(e.target.checked); changePage(0); }} /> Unread only</label>
                    <button type="button" disabled={isLoading || !!pending} onClick={refetch} className="underline">Refresh notifications</button>
                </div>
                <NotificationPreferences user={user} onReadAll={()=>{setOffset(0);refetch();}}/>
                {markError && <p role="alert" className="text-red-300 text-sm">{markError}</p>}

                {/* Error state */}
                {isError && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Failed to load notifications</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">{error?.message || "Could not load notifications."}</p>
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

                {/* Loading skeleton */}
                {isLoading && !isError && (
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
                {!isLoading && !isError && notifications.length > 0 && (
                    <div className="flex flex-col gap-3 mt-4">
                        {notifications.map((n) => (
                            <button
                                key={n.id}
                                onClick={() => void handleMarkRead(n.id)}
                                disabled={!!pending || n.read}
                                aria-label={`${n.title}${n.read ? ", read" : ", unread"}`}
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

                {!isLoading && !isError && data.total > 0 && (
                    <div className="flex items-center justify-between gap-2 text-sm">
                        <button type="button" disabled={offset === 0 || !!pending} onClick={() => changePage(Math.max(0, offset - PAGE_SIZE))} className="underline disabled:opacity-40">Previous</button>
                        <span>{Math.min(offset + 1, data.total)}–{Math.min(offset + notifications.length, data.total)} of {data.total}</span>
                        <button type="button" disabled={offset + PAGE_SIZE >= data.total || !!pending} onClick={() => changePage(offset + PAGE_SIZE)} className="underline disabled:opacity-40">Next</button>
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !isError && notifications.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl mt-4">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Bell className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No notifications yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                {unreadOnly ? "No unread notifications in this history." : "New saved notifications will appear here."}
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
