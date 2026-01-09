"use client";
import { useEffect, useRef, useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { faqs } from "@/lib/data";

export function ComboboxDemo({
    value,
    setValue,
}: {
    value: string;
    setValue: React.Dispatch<React.SetStateAction<string>>;
}) {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Close on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (
                wrapperRef.current &&
                !wrapperRef.current.contains(e.target as Node)
            ) {
                setOpen(false);
            }
        };
        document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, []);

    const filtered = faqs.filter((item) =>
        item.type.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div
            ref={wrapperRef}
            className="relative w-full flex justify-center"
        >
            {/* Trigger */}
            <button
                onClick={() => setOpen((p) => !p)}
                className="
          w-[90%] h-[10vh]
          flex items-center justify-between
          rounded-lg
          bg-[#1d1c1cff]
          border-1 border-[#7F7F7F]
          px-4
          opacity-90
          cursor-pointer
        "
            >
                <p className="text-[#6F6F6F] text-xl font-normal">
                    {value || "Select Category"}
                </p>

                <ChevronsUpDown
                    className={`h-6 w-8 text-white transition-transform duration-300 ${open ? "rotate-180" : "rotate-0"
                        }`}
                />
            </button>

            {/* Dropdown */}
            <div
                className={`
          absolute top-[110%]
          w-[90%]
          mx-auto
          rounded-lg
          bg-[#1d1c1cff]
          border border-white
          z-[99999]
          overflow-hidden
          transition-all duration-300 ease-in-out
          ${open ? "max-h-[420px] opacity-100" : "max-h-0 opacity-0"}
        `}
            >
                {/* Search input */}
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Select Category"
                    className="
            w-full
            bg-[#1d1c1cff]
            px-5 py-4
            text-white text-2xl font-thin
            outline-none
            border-b border-white
          "
                />

                {/* List */}
                <ul className="max-h-[500px] overflow-y-auto">
                    {filtered.map((item) => (
                        <li
                            key={item.type}
                            onClick={() => {
                                setValue(item.type);
                                setOpen(false);
                                setSearch("");
                            }}
                            className="
                flex items-center
                gap-5
                h-[8vh]
                px-5
                my-2
                text-xl text-white font-normal
                rounded-md
                cursor-pointer
                hover:bg-[#2a2929]
                transition-colors
              "
                        >
                            <Check
                                className={`h-4 w-4 text-white ${value === item.type ? "opacity-100" : "opacity-0"
                                    }`}
                            />
                            {item.type}
                        </li>
                    ))}

                    {filtered.length === 0 && (
                        <li className="px-5 py-4 text-gray-400">
                            No results found
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
}
