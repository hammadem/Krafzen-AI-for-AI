"use client"
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileDown, SearchIcon } from "lucide-react";
import { useState } from "react";

// TODO: Wire to real API when endpoint is ready
// Expected: GET /api/v1/exports?user_id=...
// Expected response shape: [{ id, filename, format, status, created_at, project_name, download_url }]

export default function Exports() {
    const [isLoading] = useState(false);
    const [exports] = useState<unknown[]>([]);

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Exports</h1>

                {/* Search + Format Filter */}
                <span className="flex flex-col sm:flex-row gap-4 text-[#8F8F8F]">
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border border-[#8F8F8F] rounded-[10px] w-full transition">
                        <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                        <Input
                            type="text"
                            placeholder="Search exports..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    <Select>
                        <SelectTrigger className="w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                            <SelectValue placeholder="All Formats" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectItem value="all">All Formats</SelectItem>
                                <SelectItem value="dwg">DWG</SelectItem>
                                <SelectItem value="dxf">DXF</SelectItem>
                                <SelectItem value="pdf">PDF</SelectItem>
                                <SelectItem value="svg">SVG</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </span>

                {/* Loading skeleton */}
                {isLoading && (
                    <div className="flex flex-col gap-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="skeleton h-20 w-full rounded-[10px]" />
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && exports.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <FileDown className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No exports yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Your exported CAD files will appear here once you generate them.
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
