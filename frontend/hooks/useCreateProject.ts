import { useCallback, useRef, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { createAProject } from '@/lib/api/api';
import { useDashboard } from '@/context/DashboardContext';
import { useFetchProjects } from './useFetchProjects';

export function useCreateProject(
    setFile?: (file: string) => void,
    setInput?: (input: string) => void
) {
    const { forceRefetch } = useFetchProjects();
    const { user, setCurrentProject } = useAuth();
    const { setUserAction } = useDashboard();
    const router = useRouter();
    const controllerRef = useRef<AbortController | null>(null);
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);

    const cancel = useCallback(() => {
        if (!controllerRef?.current) return;

        controllerRef.current?.abort();
        controllerRef.current = null;
        setStatus("aborted");
    }, [setStatus]);

    const createProject = useCallback(
        async (input: string) => {
            setUserAction(true);

            // avoid deduplication to delete ongoing requests
            controllerRef.current?.abort();

            const controller = new AbortController();
            controllerRef.current = controller;

            if (!input.trim()) setApiError({
                type: "INVALID",
                message: "Input field cannot be empty"
            });

            setStatus("prompting");
            // the above means prompt being sent we could use recording if recording is happening
            // using it at center removes multiboolean dependency

            const { error, ok, data } = await createAProject(user, input, controller);

            if (ok) {
                const project = data as ProjectDetails;
                setCurrentProject(project);
                forceRefetch();
                setStatus("success");
                if (setInput && setFile) {
                    setInput("");
                    setFile("");
                }
                router.push(`/workspace/id/${project.id}`);
            } else {
                setStatus("error");
                setApiError(error);
            }

            controllerRef.current = null;
        }, [setCurrentProject, setInput, setFile, setUserAction, forceRefetch, router, user, setStatus, setApiError]);

    return {
        cancel,
        createProject,
        status,
        apiError
    };
}