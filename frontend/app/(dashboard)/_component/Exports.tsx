import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download, RotateCcw, SearchIcon, Trash2 } from "lucide-react";
import { ExportHistory } from "./Examples";
import { useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export default function Exports() {
    const [currentExp, setCurrentExp] = useState<number>(-1);

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Exports</h1>

                <span className="flex gap-4 text-[#8F8F8F]">
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border-1 border-[#8F8F8F] rounded-[10px] w-full focus-within:none transition">
                        <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                        <Input
                            type="text"
                            placeholder="Search exports..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    <Select>
                        <SelectTrigger className="w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                            <SelectValue placeholder="All Categories" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectLabel>Fruits</SelectLabel>
                                <SelectItem value="apple">Apple</SelectItem>
                                <SelectItem value="banana">Banana</SelectItem>
                                <SelectItem value="blueberry">Blueberry</SelectItem>
                                <SelectItem value="grapes">Grapes</SelectItem>
                                <SelectItem value="pineapple">Pineapple</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>

                    <Select>
                        <SelectTrigger className="w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                            <SelectValue placeholder="All Status" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                <SelectLabel>Fruits</SelectLabel>
                                <SelectItem value="apple">Apple</SelectItem>
                                <SelectItem value="banana">Banana</SelectItem>
                                <SelectItem value="blueberry">Blueberry</SelectItem>
                                <SelectItem value="grapes">Grapes</SelectItem>
                                <SelectItem value="pineapple">Pineapple</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>

                </span>

                <div className="flex gap-4">
                    <div className="w-full flex flex-col gap-4">
                        {
                            [...Array(10)].map((_, ind) => (
                                <div key={ind} onClick={() => setCurrentExp(ind)} className="cursor-pointer">
                                    <ExportHistory ind={ind} currentExp={currentExp} />
                                </div>
                            ))
                        }
                    </div>

                    <div className={classNames("bg-[#2F2F2F] p-4 rounded-[10px] h-[115vh]", currentExp < 0 ? "hidden" : "block")}>
                        <span className="flex flex-col gap-4">
                            <h1 className="text-white font-semibold text-[4vh]">Exports</h1>
                            <Image
                                src="/dashboard/tempexample.png"
                                width={500}
                                height={500}
                                alt="Export Details Image"
                            />

                            <span>
                                <p className="text-[#8F8F8F]">File Name</p>
                                <p>project_alpha_floorplan.dwg</p>
                            </span>

                            <span className="flex items-center justify-between">
                                <span className="flex flex-col w-full items-start gap-6">
                                    <span>
                                        <p className="text-[#8F8F8F]">Format</p>
                                        <p>DWG</p>
                                    </span>
                                    <span>
                                        <p className="text-[#8F8F8F]">Status</p>
                                        <Badge variant="secondary" className="bg-[#FC932A]/15 text-[#FC932A]">
                                            <span className="rounded-full h-2 w-2 bg-[#FC932A]" />
                                            Pending
                                        </Badge>
                                    </span>
                                </span>

                                <span className="flex w-full flex-col items-start gap-6">
                                    <span>
                                        <p className="text-[#8F8F8F]">Date</p>
                                        <p>2025-10-27</p>
                                    </span>
                                    <span>
                                        <p className="text-[#8F8F8F]">Project</p>
                                        <p>Office Redesign</p>
                                    </span>
                                </span>

                            </span>

                            <span className="flex flex-col gap-4 py-2">
                                <Button
                                    className="bg-black text-white hover:bg-black"
                                >
                                    <Download />
                                    Download
                                </Button>
                                <Button
                                    className="bg-transparent text-white hover:bg=transparent bg-[#3F3F3F] flex items-center"
                                >
                                    <RotateCcw />
                                    Re-export
                                </Button>

                                <Button
                                    className="text-red-700 bg-transparent hover:bg=transparent flex items-center"
                                >
                                    <Trash2 className="text-red-700" />
                                    Delete Export
                                </Button>
                            </span>
                        </span>
                    </div>
                </div>

            </div>
        </div>
    )
}