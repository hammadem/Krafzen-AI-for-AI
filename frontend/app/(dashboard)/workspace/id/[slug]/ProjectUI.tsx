"use client"
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/context/DashboardContext";
import { useApiResource } from "@/hooks/useApiResource";
import { getAProject, getAllJobs, getDashboardActivity } from "@/lib/api/api";
import FilesPanel from "@/components/FilesPanel";
import { AlertCircle, Check, Copy, Mic, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";

interface ProjectActivityEvent {
    id: string;
    event_id?: string | null;
    message: string;
    actor_name?: string | null;
    occurred_at?: string | null;
}

interface ProjectActivityPage {
    events: ProjectActivityEvent[];
    total: number;
    has_more: boolean;
}

const PROJECT_ACTIVITY_PAGE_SIZE = 50;

function parseProjectActivity(raw: unknown): ProjectActivityPage {
    if (
        typeof raw !== "object" ||
        raw === null ||
        !("events" in raw) ||
        !Array.isArray(raw.events)
    ) {
        return { events: [], total: 0, has_more: false };
    }

    return {
        events: raw.events.filter(
            (event): event is ProjectActivityEvent =>
                typeof event === "object" &&
                event !== null &&
                "id" in event &&
                typeof event.id === "string" &&
                "message" in event &&
                typeof event.message === "string"
        ),
        total: "total" in raw && typeof raw.total === "number" ? raw.total : 0,
        has_more: "has_more" in raw && raw.has_more === true,
    };
}

function ProjectActivityPanel({ projectId }: { projectId: string }) {
    const { user } = useAuth();
    const {
        data: activityPage,
        isLoading,
        isError,
        error,
        refetch,
        setData,
    } = useApiResource<ProjectActivityPage>({
        fetcher: (authenticatedUser) =>
            getDashboardActivity(authenticatedUser, {
                projectId,
                limit: PROJECT_ACTIVITY_PAGE_SIZE,
                offset: 0,
            }),
        select: (raw) => parseProjectActivity(raw),
        fallback: { events: [], total: 0, has_more: false },
    });
    const [loadingMore, setLoadingMore] = useState(false);
    const [loadError, setLoadError] = useState<string | null>(null);

    const loadMore = async () => {
        if (!user || loadingMore || !activityPage.has_more) return;
        setLoadingMore(true);
        setLoadError(null);
        try {
            const result = await getDashboardActivity(user, {
                projectId,
                limit: PROJECT_ACTIVITY_PAGE_SIZE,
                offset: activityPage.events.length,
            });
            if (!result.ok) {
                throw new Error(result.error?.message || "Could not load more project activity.");
            }
            const nextPage = parseProjectActivity(result.data);
            if (!nextPage || !Array.isArray(nextPage.events)) {
                throw new Error("The project activity response was invalid.");
            }
            setData((current) => {
                const seen = new Set(
                    current.events.map((event) => event.event_id || event.id)
                );
                const newEvents = nextPage.events.filter(
                    (event) => !seen.has(event.event_id || event.id)
                );
                return {
                    ...current,
                    events: [...current.events, ...newEvents],
                    total: current.events.length + newEvents.length,
                    has_more: nextPage.has_more,
                };
            });
        } catch (error) {
            setLoadError(
                error instanceof Error
                    ? error.message
                    : "Could not load more project activity."
            );
        } finally {
            setLoadingMore(false);
        }
    };

    return (
        <section aria-label="Project activity" className="rounded-xl border border-white/10 bg-[#111722] p-5">
            <h2 className="text-lg font-semibold text-white">Project Activity</h2>
            {isLoading ? (
                <p className="mt-3 text-sm text-[#94a3b8]">Loading activity...</p>
            ) : isError ? (
                <div className="mt-3">
                    <p role="alert" className="text-sm text-red-300">
                        {error?.message || "Could not load project activity."}
                    </p>
                    <button
                        type="button"
                        onClick={refetch}
                        className="mt-2 text-sm text-[#54e3b5] hover:text-white"
                    >
                        Try again
                    </button>
                </div>
            ) : activityPage.events.length ? (
                <ol className="mt-3 divide-y divide-white/10">
                    {activityPage.events.map((event) => (
                        <li key={event.event_id || event.id} className="py-3 first:pt-0 last:pb-0">
                            <p className="text-sm text-white">{event.message}</p>
                            <p className="mt-1 text-xs text-[#94a3b8]">
                                {event.actor_name || "System"}
                                {event.occurred_at
                                    ? ` - ${new Date(event.occurred_at).toLocaleString()}`
                                    : ""}
                            </p>
                        </li>
                    ))}
                </ol>
            ) : (
                <p className="mt-3 text-sm text-[#94a3b8]">No activity recorded for this project yet.</p>
            )}
            {!isLoading && !isError && activityPage.has_more && (
                <div className="mt-4 flex flex-col items-center gap-2">
                    {loadError && <p role="alert" className="text-sm text-red-300">{loadError}</p>}
                    <button
                        type="button"
                        onClick={() => void loadMore()}
                        disabled={loadingMore}
                        className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-white hover:bg-white/5 disabled:opacity-50"
                    >
                        {loadingMore ? "Loading…" : loadError ? "Try again" : "Load more"}
                    </button>
                </div>
            )}
        </section>
    );
}

function ProjectFilesPanel({ projectId }: { projectId: string }) {
    const { data: jobs, isLoading, isError, error } = useApiResource<JobDetails[]>({
        fetcher: (authenticatedUser) => getAllJobs(authenticatedUser, projectId),
        select: (raw) => Array.isArray(raw) ? raw as unknown as JobDetails[] : [],
        fallback: [],
    });

    return (
        <section aria-label="Project files" className="rounded-xl border border-white/10 bg-[#111722] p-5">
            <h2 className="text-lg font-semibold text-white">Files</h2>
            {isLoading ? (
                <p className="mt-3 text-sm text-[#94a3b8]">Loading project files...</p>
            ) : isError ? (
                <p role="alert" className="mt-3 text-sm text-red-300">
                    {error?.message || "Could not load project files."}
                </p>
            ) : jobs.length ? (
                <div className="mt-4 space-y-5">
                    {jobs.map((job) => (
                        <FilesPanel key={job.id} jobId={job.id} />
                    ))}
                </div>
            ) : (
                <p className="mt-3 text-sm text-[#94a3b8]">No files are linked to this project yet.</p>
            )}
        </section>
    );
}

export default function ProjectUI({ slug }: { slug: string }) {
    const { currentProject, user, setCurrentProject } = useAuth();
    const { setUserAction } = useDashboard();
    const [copied, setCopied] = useState<boolean>(false);
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);
    const [retryCount, setRetryCount] = useState<number>(0);

    // here keeping this with its own state managment is better same should be done with project history
    useEffect(() => {
        if (!user || !slug) return;

        let isMounted = true;

        const loadProject = async () => {
            try {
                setStatus("inprogress");
                setApiError(null);
                setUserAction(true);

                const { data, error, ok } = await getAProject(user, slug);

                if (!ok || error) {
                    setApiError(error);
                    setStatus("error");
                    return;
                }

                if (isMounted) {
                    setCurrentProject(data as ProjectDetails);
                    setStatus("success");
                }
            } catch {
                if (isMounted) {
                    setStatus("error");
                    setApiError({
                        message: "Unexpected error",
                        type: "UNKNOWN"
                    })
                }
            } finally {
                if (isMounted) {
                    setUserAction(true);
                }
            }
        };

        loadProject();

        return () => {
            isMounted = false;
        };
    }, [user, slug, retryCount, setCurrentProject, setUserAction]);

    if (status === "error") {
        return (
            <div className="flex flex-col items-center justify-center w-full h-full gap-4 text-white">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-medium">Failed to load project</h3>
                    <p className="text-[#94a3b8] text-sm mt-1">
                        {apiError?.message ?? "Something went wrong. Please try again."}
                    </p>
                </div>
                <Button
                    type="reset"
                    onClick={() => setRetryCount((c) => c + 1)}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                >
                    <RefreshCw className="w-4 h-4" />
                    Try again
                </Button>
            </div>
        );
    }

    if (status === "inprogress" || !currentProject) {
        return (
            <div className="w-full h-full flex flex-col gap-6 p-8 bg-black">
                {/* User message skeleton */}
                <div className="flex justify-end">
                    <div className="skeleton h-16 w-[60%] rounded-[15px]" />
                </div>
                {/* AI response skeleton */}
                <div className="flex justify-start">
                    <div className="skeleton h-24 w-[70%] rounded-[15px]" />
                </div>
            </div>
        );
    }

    return (
        <>
            {
                currentProject !== null
                &&
                <div className="w-full h-full flex items-start justify-end overflow-y-auto custom-scrollbar2 bg-black">
                    <div className="w-[95%] sm:w-[80%] items-end sm:items-center flex flex-col gap-4 h-1000 bg-black">

                        {/** Here The Data from API Can Be Shown */}
                        <div className="w-[90%] bg-black mr-4 sm:mr-0">

                            <div className="flex self-end flex-col text-[2vh] bg-black mb-1">
                                <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-end sm:self-end">
                                    <h1 className="text-white font-normal">{currentProject?.input_text}</h1>
                                </div>
                                <span className="self-end flex gap-2 mt-3">
                                    <Mic className="cursor-pointer"
                                        onClick={() => {

                                        }}
                                    />
                                    {copied ? (
                                        <Check className="text-white cursor-pointer" />
                                    ) : (
                                        <Copy
                                            className="cursor-pointer"
                                            onClick={() => {
                                                navigator.clipboard.writeText(currentProject?.input_text || "");
                                                toast.dark("Copied Successfully");

                                                setCopied(true);
                                                setTimeout(() => setCopied(false), 1500); // revert after 1.5s
                                            }}
                                        />
                                    )}

                                    {currentProject?.time}
                                </span>
                            </div>


                            <div className="flex self-start flex-col justify-start gap-4 bg-black mb-1 mt-[4vh]">
                                <div className="bg-[#434343] p-6 w-[90%] sm:w-[80%] rounded-[15px] flex flex-col self-end sm:self-start">
                                    {currentProject?.image_url ? (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img
                                            src={currentProject.image_url}
                                            alt={currentProject.input_text || "Generated project"}
                                            className="w-full rounded-xl border border-white/10 bg-black object-contain"
                                        />
                                    ) : (
                                        <p className="text-[#94a3b8] text-sm">
                                            No generated image is linked to this project yet.
                                        </p>
                                    )}
                                </div>
                            </div>

                        </div>

                        <div className="w-[90%] mr-4 sm:mr-0 space-y-5">
                            <ProjectActivityPanel
                                key={currentProject.id}
                                projectId={currentProject.id}
                            />
                            <ProjectFilesPanel key={slug} projectId={slug} />
                        </div>
                    </div>
                </div>
            }
        </>
    )
}
