import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { createAProject } from '@/lib/api/api';
import { useDashboard } from '@/context/DashboardContex';
import { useFetchProjects } from './useFetchProjects';

export function useCreateProject() {
    const { forceRefetch } = useFetchProjects();
    const { user, setCurrentProject } = useAuth();
    const { isPrompting, setisPromptingSend, setUserAction } = useDashboard();
    const router = useRouter();
    const [error, setError] = useState<string | null>(null);

    const createProject = async (input: string, setInput: (input: string) => void) => {
        setUserAction(true);
        setisPromptingSend(true);
        setInput("");

        if (!user) setError("Not Authorized User");
        if (!input.trim()) setError("Input cannot be empty");

        if (error !== null) {
            setisPromptingSend(false);
            return {
                error,
                isPrompting,
                project: null
            }
        }
        const res = await createAProject(user, input);
        if (!res.ok) setError(res.error || "Unexpected Error Occured");

        const project = res.data as ProjectDetails;
        setCurrentProject(project);

        forceRefetch();

        router.push(`/dashboard/id/${project.id}`);
        setisPromptingSend(false);

        return {
            error,
            isPrompting,
            project,
        };
    };

    return {
        createProject,
        isPrompting,
        error,
    };
}