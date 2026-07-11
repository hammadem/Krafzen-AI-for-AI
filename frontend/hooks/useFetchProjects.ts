// this needs to be optimized yet
import { useState, useEffect, useCallback } from "react";
import { getAllProjects } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";
import { deleteCacheByPrefix } from "@/lib/api/cache";

const DEFAULT_LIMIT = 20;

export function useFetchProjects(initialPage = 1) {
    const { user } = useAuth();
    const [projects, setProjects] = useState<ProjectDetails[]>([]);
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);
    const [page, setPage] = useState<number>(initialPage);
    const [hasMore, setHasMore] = useState<boolean>(true);

    const fetchProjects = useCallback(async (pageToFetch = 1) => {
        if (!user?.userId) return;
        setStatus("inprogress");
        const { ok, data, error } = await getAllProjects(user, user.userId, pageToFetch, DEFAULT_LIMIT);

        if (ok) {
            // Handle both response shapes:
            // 1. Array directly: ProjectDetails[]
            // 2. Object with key: { projects: [...] } or { data: [...] }
            let items: ProjectDetails[] = [];

            if (Array.isArray(data)) {
                items = data as ProjectDetails[];
            } else if (data && typeof data === "object") {
                const obj = data as Record<string, unknown>;
                const arr = obj.projects ?? obj.data ?? obj.items ?? [];
                items = Array.isArray(arr) ? (arr as ProjectDetails[]) : [];
            }

            setProjects(items);
            setHasMore(items.length === DEFAULT_LIMIT);
            setStatus("success");
        } else {
            setStatus("error");
            setApiError(error);
        }

    }, [user]);

    useEffect(() => {
        const load = async () => await fetchProjects(page);
        load();
    }, [fetchProjects, page]);

    const forceRefetch = useCallback(() => {
        if (!user) return;
        // Clear every cached projects-list page (any params) so a freshly created/updated
        // project shows immediately — robust to page/limit/URL changes, unlike an exact key.
        deleteCacheByPrefix(`GET:/api/v1/projects`);
        fetchProjects(page);
    }, [user, fetchProjects, page]);

    const nextPage = useCallback(() => {
        if (hasMore) setPage((p) => p + 1);
    }, [hasMore]);

    const prevPage = useCallback(() => {
        setPage((p) => Math.max(1, p - 1));
    }, []);

    return { projects, forceRefetch, status, apiError, page, hasMore, nextPage, prevPage };
}
