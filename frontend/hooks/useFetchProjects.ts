import { useState, useEffect, useCallback, useRef } from "react";
import { getAllProjects } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";

const DEFAULT_LIMIT = 20;

/** Paginated owner-scoped catalog. Old requests cannot overwrite a new search or session. */
export function useFetchProjects(initialPage = 1, search = "", archived = false, projectType?: ProjectType, lifecycleStage?: ProjectStage) {
    const { user } = useAuth();
    const [projects, setProjects] = useState<ProjectDetails[]>([]);
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);
    const [page, setPage] = useState(initialPage);
    const [hasMore, setHasMore] = useState(false);
    const [reload, setReload] = useState(0);
    const [loadedScope, setLoadedScope] = useState<string | null>(null);
    const generation = useRef(0);
    const principal = user?.userId;
    const token = user?.access_token;
    const scope = principal && token ? JSON.stringify([principal, page, search, archived, projectType, lifecycleStage]) : null;

    useEffect(() => {
        const current = ++generation.current;
        if (!principal || !token || !user || !scope) {
            setProjects([]); setHasMore(false); setStatus("idle"); setApiError(null); setLoadedScope(null);
            return;
        }
        setStatus("inprogress");
        setApiError(null);
        const timer = window.setTimeout(async () => {
            try {
            const response = await getAllProjects(user, principal, page, DEFAULT_LIMIT, {search, archived, projectType, lifecycleStage});
            if (generation.current !== current) return;
            setLoadedScope(scope);
            if (!response.ok) {
                setProjects([]); setHasMore(false); setStatus("error"); setApiError(response.error);
                return;
            }
            const raw = response.data;
            const candidate = Array.isArray(raw) ? raw : raw && typeof raw === "object"
                ? (raw as Record<string, unknown>).projects ?? (raw as Record<string, unknown>).data ?? (raw as Record<string, unknown>).items
                : null;
            if (!Array.isArray(candidate)) {
                setProjects([]); setHasMore(false); setStatus("error");
                setApiError({type: "UNKNOWN", message: "Invalid project list response"});
                return;
            }
            const items = candidate as ProjectDetails[];
            if (items.length === 0 && page > 1) {
                setPage(page - 1);
                return;
            }
            setProjects(items);
            setHasMore(items.length === DEFAULT_LIMIT);
            setStatus("success");
            } catch {
                if (generation.current !== current) return;
                setProjects([]); setHasMore(false); setLoadedScope(scope); setStatus("error");
                setApiError({type: "UNKNOWN", message: "Could not load projects. Please retry."});
            }
        }, search.trim() ? 250 : 0);
        return () => { window.clearTimeout(timer); ++generation.current; };
        // Authorization depends on the actual principal/token rather than unrelated profile refreshes.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [scope, token, reload]);

    const forceRefetch = useCallback(() => setReload((value) => value + 1), []);
    const isCurrent = !!scope && loadedScope === scope;
    const nextPage = useCallback(() => { if (isCurrent && hasMore) setPage((p) => p + 1); }, [isCurrent, hasMore]);
    const prevPage = useCallback(() => setPage((p) => Math.max(1, p - 1)), []);
    const firstPage = useCallback(() => setPage(1), []);
    return { projects: isCurrent ? projects : [], forceRefetch, status: !scope ? "idle" as const : isCurrent ? status : "inprogress" as const,
        apiError: isCurrent ? apiError : null, page, hasMore: isCurrent && hasMore, nextPage, prevPage, firstPage };
}
