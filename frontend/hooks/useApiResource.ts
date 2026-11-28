// Reusable data-fetching hook for authenticated dashboard resources.
//
// Every dashboard page (activity, members, notifications, templates, archive…)
// repeats the same shape: wait for the user, fetch once, track loading/error,
// expose a retry, and cancel cleanly on unmount. This hook owns that pattern so
// the pages only describe *what* to fetch and *how* to shape the result.
//
// Usage:
//   const { data, status, error, refetch } = useApiResource<ActivityEvent[]>({
//       fetcher: (user) => getDashboardActivity(user),
//       select: (raw) => (raw as { events?: ActivityEvent[] }).events ?? [],
//       fallback: [],
//   });

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";

interface UseApiResourceOptions<T> {
    /** Calls the API layer (api.ts) and returns the standard ApiRes shape. */
    fetcher: (user: User) => Promise<ApiRes>;
    /** Pull the typed value out of the raw response payload. */
    select: (raw: ApiRes["data"]) => T;
    /** Returned for `data` until the first successful load. */
    fallback: T;
    /** Skip fetching until true (e.g. waiting on a route param). Defaults to true. */
    enabled?: boolean;
    /** Resource identity when the same component is reused for different records. */
    resourceKey?: string;
}

interface UseApiResourceResult<T> {
    data: T;
    status: ReqState;
    error: AppError | null;
    /** Re-run the fetch (used by "Try again" buttons). */
    refetch: () => void;
    /** Directly set local data — used for optimistic updates (e.g. mark-as-read). */
    setData: React.Dispatch<React.SetStateAction<T>>;
    /** Convenience flags derived from `status`. */
    isLoading: boolean;
    isError: boolean;
}

export function useApiResource<T>({
    fetcher,
    select,
    fallback,
    enabled = true,
    resourceKey = "",
}: UseApiResourceOptions<T>): UseApiResourceResult<T> {
    const { user } = useAuth();
    const [data, setData] = useState<T>(fallback);
    const [status, setStatus] = useState<ReqState>("idle");
    const [error, setError] = useState<AppError | null>(null);
    const [reloadKey, setReloadKey] = useState(0);
    const [loadedScope, setLoadedScope] = useState<string | null>(null);
    const scope = user?.userId && enabled ? user.userId + ":" + resourceKey : null;
    const token = user?.access_token;

    useEffect(() => {
        if (!enabled || !user?.userId || !token || !scope) {
            setData(fallback); setLoadedScope(null); setStatus("idle"); setError(null);
            return;
        }
        let isMounted = true;

        const load = async () => {
            setStatus("inprogress");
            setError(null);

            try {
                const res = await fetcher(user);
                if (!isMounted) return;
                if (res.ok) {
                    setData(select(res.data));
                    setLoadedScope(scope);
                    setStatus("success");
                } else {
                    setData(fallback); setLoadedScope(scope);
                    setError(res.error ?? { type: "UNKNOWN", message: "Something went wrong." });
                    setStatus("error");
                }
            } catch {
                if (!isMounted) return;
                setData(fallback); setLoadedScope(scope);
                setError({type:"UNKNOWN",message:"Unable to load this resource. Please retry."}); setStatus("error");
            }
        };

        load();
        return () => {
            isMounted = false;
        };
        // `fetcher`/`select` are defined inline by callers, so we intentionally
        // key the effect on the user + manual reload trigger instead.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [scope, token, reloadKey, enabled]);

    const refetch = useCallback(() => setReloadKey((k) => k + 1), []);

    return {
        data: scope && loadedScope === scope ? data : fallback,
        status: scope && loadedScope !== scope && status !== "error" ? "inprogress" : status,
        error: loadedScope === scope ? error : null,
        refetch,
        setData,
        isLoading: !!scope && (status === "inprogress" || loadedScope !== scope),
        isError: !!scope && loadedScope === scope && status === "error",
    };
}
