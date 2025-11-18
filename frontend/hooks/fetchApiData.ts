import { toast } from "react-toastify";
import { formatTime, formatDate } from "@/lib/utils";

export async function fetchProjects({ user, project }: { user: User | null, project: string }) {
    const fetchPromptHistory = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/projects`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${user?.userId}`,  // if needed,
                    "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
                },
                body: JSON.stringify({
                    user_id: user?.userId,
                    input_text: project
                })
            });
            const response = await res.json();
            if (res.ok) {
                toast.dark("Successfully fetched response");
            } else {
                toast.error(response.message);
            }
        } catch (err) {
            console.log(err);
            toast.error("Server Error Occured");
        }
    }
    fetchPromptHistory();
}

export async function fetchPromptHistory({ user, setHistory, setProjects }: { user: User | null, setHistory: (value: HistoryData[]) => void, setProjects: (value: ProjectDetails[]) => void }) {
    try {
        const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/v1/projects?user_id=${user?.userId}`,
            {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${user?.userId}`,
                    "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
                }
            }
        );
        const response = await res.json();

        if (res.ok) {
            const grouped: HistoryData[] = [];

            response.forEach((item: ProjectDetails) => {
                const isoDate = item.created_at.split("T")[0];        // 2025-11-16
                const displayDate = formatDate(item.created_at);      // 16th Nov 2025
                const displayTime = formatTime(item.created_at);      // 07:21 PM

                let group = grouped.find(g => g.iso === isoDate);

                if (!group) {
                    group = {
                        iso: isoDate,
                        date: displayDate,
                        searches: []
                    };
                    grouped.push(group);
                }

                group.searches.push({
                    title: item.input_text,
                    time: displayTime,
                    isoTime: item.created_at,   // <-- Add raw timestamp for time sorting
                    chats: item?.dxf_url
                });
            });
            // Sort groups by date (newest → oldest)
            grouped.sort((a, b) =>
                new Date(b.iso).getTime() - new Date(a.iso).getTime()
            );
            // Sort searches *inside each day* by newest time first
            grouped.forEach(group => {
                group.searches.sort((a, b) =>
                    new Date(b.isoTime).getTime() - new Date(a.isoTime).getTime()
                );
            });
            setHistory(grouped);
            setProjects(response);
            toast.success("Successfully fetched response");
        } else {
            toast.error(response?.message);
        }
    } catch (err) {
        console.log(err);
        toast.error("Server Error");
    }
};

export const sendPromptRequest = async ({ setIsPromptSend, setUserAction, user, input, setInput, setAudioURL, setFile }: {
    setIsPromptSend: (value: boolean) => void,
    setUserAction: (value: boolean) => void;
    user: User | null;
    input: string;
    setInput: (value: string) => void;
    setAudioURL: (value: string) => void;
    setFile: (value: string) => void;
}) => {
    setIsPromptSend(true);
    setUserAction(true);

    try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/projects`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${user?.userId}`,  // if needed,
                "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
            },
            body: JSON.stringify({
                user_id: user?.userId,          // <-- IMPORTANT
                input_text: input
            })
        });

        const response = await res.json();

        if (res.ok) {
            toast.success("Succesfully fetched response");
        } else {
            console.log(res);
            toast.error(response.message);
        }

        setIsPromptSend(false);
        setInput("");
        setAudioURL("");
        setFile("");

    } catch (err) {
        console.log(err);
        toast.error("Server Error");
    } finally {
        setIsPromptSend(false);
        setInput("");
        setAudioURL("");
        setFile("");
    }
}
