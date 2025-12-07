"use client";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function History({ data, loading }: { data: HistoryData[], loading: boolean }) {
    const pathname = usePathname();

    return (
        <div className="text-[#919191] text-[4vh] flex flex-col">
            <h1 className="font-semibold">History</h1>

            {loading ? (
                <div className="flex flex-col gap-6">
                    {/* Skeleton for 2–3 history sections */}
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="flex flex-col gap-3">
                            {/* Date Skeleton */}
                            <Skeleton className="w-32 h-4 rounded-md" />

                            {/* Title/time pairs */}
                            <div className="flex items-center justify-between gap-2">
                                <Skeleton className="w-[70%] h-5 rounded-md" />
                                <Skeleton className="w-12 h-4 rounded-md" />
                            </div>

                            <div className="flex items-center justify-between gap-2">
                                <Skeleton className="w-[60%] h-5 rounded-md" />
                                <Skeleton className="w-10 h-4 rounded-md" />
                            </div>

                            <div className="flex items-center justify-between gap-2">
                                <Skeleton className="w-[80%] h-5 rounded-md" />
                                <Skeleton className="w-16 h-4 rounded-md" />
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                data.map(info => (
                    <div key={info?.searches[0].id.toString() + "Date"} className="flex flex-col">
                        <p className="text-[2vh] font-semibold">{info.date}</p>
                        {info.searches.map(detail => {
                            const isActive = pathname === `/dashboard/id/${detail.id}`;

                            return (
                                <Link
                                    aria-label="Link to project details"
                                    href={`/dashboard/id/${detail.id}`}
                                    key={detail?.id}
                                    className={isActive ? "flex items-center justify-between cursor-pointer rounded py-1 px-1 bg-[#292929]" : "rounded py-1 flex items-center justify-between cursor-pointer"}
                                >
                                    <p className="text-[2.5vh] font-normal text-white w-[70%] truncate">
                                        {detail.title}
                                    </p>
                                    <p className="text-[2vh] font-semibold text-[#616161]">
                                        {detail.time}
                                    </p>
                                </Link>
                            )
                        }
                        )}
                    </div>
                ))
            )}
        </div>

    );
}