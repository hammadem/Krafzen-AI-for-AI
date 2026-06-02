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
}: UseApiResourceOptions<T>): UseApiResourceResult<T> {
    const { user } = useAuth();
    const [data, setData] = useState<T>(fallback);
    const [status, setStatus] = useState<ReqState>("idle");
    const [error, setError] = useState<AppError | null>(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        if (!enabled || !user?.userId) return;
        let isMounted = true;

        const load = async () => {
            setStatus("inprogress");
            setError(null);

            const res = await fetcher(user);
            if (!isMounted) return;

            if (res.ok) {
                setData(select(res.data));
                setStatus("success");
            } else {
                setError(res.error ?? { type: "UNKNOWN", message: "Something went wrong." });
                setStatus("error");
            }
        };

        load();
        return () => {
            isMounted = false;
        };
        // `fetcher`/`select` are defined inline by callers, so we intentionally
        // key the effect on the user + manual reload trigger instead.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, reloadKey, enabled]);

    const refetch = useCallback(() => setReloadKey((k) => k + 1), []);

    return {
        data,
        status,
        error,
        refetch,
        setData,
        isLoading: status === "inprogress",
        isError: status === "error",
    };
}
