import { useState, useEffect, useCallback } from "react";
import { getAllProjects } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";
import { apiCache } from "@/lib/api/cache";

export function useFetchProjects() {
    const { user } = useAuth();
    const [error, setError] = useState<string | null>(null);
    const [projects, setProjects] = useState<ProjectDetails[]>([]);

    const fetchProjects = useCallback(async () => {
        if (!user) {
            setError("Not Authorized User");
            return;
        }
        setError(null);
        setProjects([]);

        const cacheKey = `GET:/api/v1/projects?user_id=${user?.userId}`;
        if (apiCache.has(cacheKey)) {
            setProjects(apiCache.get(cacheKey)?.data as ProjectDetails[]);
            return;
        }

        const res = await getAllProjects(user, user.userId!);
        if (res.ok) setProjects(res.data as ProjectDetails[]);
        else setError(res.error);
    }, [user]);

    useEffect(() => {
        const load = async () => await fetchProjects();
        load();
    }, [fetchProjects]);

    const forceRefetch = useCallback(() => {
        if (!user) return;
        apiCache.delete(`GET:/api/v1/projects?user_id=${user?.userId}`);
        fetchProjects();
    }, [user, fetchProjects]);

    return { projects, error, forceRefetch };
}
