"use client";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LayoutTemplate, SearchIcon } from "lucide-react";
import { useState } from "react";
import NavHeader from "@/components/NavHeader";

// TODO: Wire to real API when endpoint is ready
// Expected: GET /api/v1/templates
// Expected response shape: [{ id, name, category, preview_url, description }]

export default function Templates() {
    const [isLoading, setIsLoading] = useState(false);
    const [templates] = useState<unknown[]>([]);

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
                            placeholder="Search templates..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    <Select>
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

                {/* Empty state */}
                {!isLoading && templates.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <LayoutTemplate className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No templates yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Pre-designed CAD templates will appear here soon.
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
        </div>
    );
}
