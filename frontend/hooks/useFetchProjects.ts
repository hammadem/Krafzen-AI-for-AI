// this needs to be optimized yet
import { useState, useEffect, useCallback } from "react";
import { getAllProjects } from "@/lib/api/api";
import { useAuth } from "@/context/AuthContext";
import { apiCache } from "@/lib/api/cache";
import { useApiStateProvider } from "@/context/ApiStateContext";

export function useFetchProjects() {
    const { user } = useAuth();
    const { setStatus, setApiError } = useApiStateProvider();
    const [projects, setProjects] = useState<ProjectDetails[]>([]);

    const fetchProjects = useCallback(async () => {
        setStatus("inprogress");
        const { ok, data, error } = await getAllProjects(user, user!.userId!);

        if (ok) {
            setProjects(data as ProjectDetails[]);
            setStatus("success");
        } else {
            setStatus("error");
            setApiError(error);
        }

    }, [user, setStatus, setApiError]);

    useEffect(() => {
        const load = async () => await fetchProjects();
        load();
    }, [fetchProjects]);

    const forceRefetch = useCallback(() => {
        if (!user) return;
        apiCache.delete(`GET:/api/v1/projects?user_id=${user?.userId}`);
        fetchProjects();
    }, [user, fetchProjects]);

    return { projects, forceRefetch };
}
