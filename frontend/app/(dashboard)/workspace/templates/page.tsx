"use client";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LayoutTemplate, SearchIcon } from "lucide-react";
import { useState, useMemo } from "react";
import Image from "next/image";
import NavHeader from "@/components/NavHeader";
import { getTemplates } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import ErrorState from "@/components/feedback/ErrorState";
import EmptyResultState from "@/components/feedback/EmptyResultState";

// Wired to GET /api/v1/templates (Yehor — endpoint pending).
// Response shape: [{ id, name, category, preview_url, description }]
// Until the endpoint ships this resolves to an empty list / error state gracefully.

interface Template {
    id: string;
    name: string;
    category: string;
    preview_url: string | null;
    description: string;
}

export default function Templates() {
    const [search, setSearch] = useState("");
    const [category, setCategory] = useState("all");

    const {
        data: templates,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<Template[]>({
        fetcher: (user) => getTemplates(user),
        select: (raw) => {
            if (Array.isArray(raw)) return raw as unknown as Template[];
            if (raw && typeof raw === "object" && "templates" in raw) {
                const list = (raw as { templates?: Template[] }).templates;
                return Array.isArray(list) ? list : [];
            }
            return [];
        },
        fallback: [],
    });

    // Client-side search + category filtering over the fetched list.
    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return templates.filter((t) => {
            const matchesCategory = category === "all" || t.category === category;
            const matchesSearch =
                !q ||
                t.name?.toLowerCase().includes(q) ||
                t.description?.toLowerCase().includes(q);
            return matchesCategory && matchesSearch;
        });
    }, [templates, search, category]);

    return (
        <div className="min-h-screen bg-[#06080d] text-white pb-20">
        <NavHeader currentNav="Templates" />
        <div className="text-white flex p-4 flex-col items-center justify-start gap-6 w-full bg-[#06080d] overflow-y-auto custom-scrollbar2">
            <div className="w-full max-w-4xl px-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Templates</h1>
                <p className="text-[#8F8F8F]">Browse and start your project with a pre-designed template.</p>

                {/* Search + Category Filter */}
                <span className="flex sm:flex-row flex-col gap-4 text-[#8F8F8F]">
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border border-[#8F8F8F] rounded-[10px] w-full transition">
                        <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                        <Input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search templates..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    <Select value={category} onValueChange={setCategory}>
                        <SelectTrigger className="w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                            <SelectValue placeholder="All Categories" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectItem value="all">All Categories</SelectItem>
                                <SelectItem value="residential">Residential</SelectItem>
                                <SelectItem value="commercial">Commercial</SelectItem>
                                <SelectItem value="industrial">Industrial</SelectItem>
                                <SelectItem value="infrastructure">Infrastructure</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </span>

                {/* Loading skeleton */}
                {isLoading && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                            <div key={i} className="skeleton h-40 w-full rounded-[10px]" />
                        ))}
                    </div>
                )}

                {/* Error state */}
                {isError && !isLoading && (
                    <ErrorState error={error} title="Couldn't load templates" onRetry={refetch} />
                )}

                {/* Templates grid */}
                {!isLoading && !isError && visible.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        {visible.map((t) => (
                            <div
                                key={t.id}
                                className="group bg-[#0F0F0F] border border-white/10 rounded-[10px] overflow-hidden hover:border-[#54e3b5]/50 transition-all cursor-pointer"
                            >
                                <div className="h-28 bg-white/5 flex items-center justify-center relative">
                                    {t.preview_url ? (
                                        <Image
                                            src={t.preview_url}
                                            alt={t.name}
                                            fill
                                            sizes="(max-width: 768px) 50vw, 25vw"
                                            className="object-cover"
                                        />
                                    ) : (
                                        <LayoutTemplate className="w-8 h-8 text-[#54e3b5]/40" />
                                    )}
                                </div>
                                <div className="p-3 flex flex-col gap-1">
                                    <h3 className="text-white text-sm font-medium line-clamp-1">{t.name}</h3>
                                    <p className="text-[#8F8F8F] text-xs capitalize">{t.category}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !isError && visible.length === 0 && (
                    <EmptyResultState
                        icon={LayoutTemplate}
                        title={templates.length === 0 ? "No templates yet" : "No matches"}
                        message={
                            templates.length === 0
                                ? "Pre-designed CAD templates will appear here soon."
                                : "Try a different search or category."
                        }
                    />
                )}

            </div>
        </div>
        </div>
    );
}
