"use client";
import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/app/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { faqs } from "@/app/lib/data";

export function ComboboxDemo({ setValue,value }: { setValue: React.Dispatch<React.SetStateAction<string>>,value:string }) {
    const [open, setOpen] = React.useState(false)

    return (
        <Popover open={open} onOpenChange={setOpen} >
            <PopoverTrigger asChild>
                <Button
                    variant="secondary"
                    role="combobox"
                    aria-expanded={open}
                    className="w-[80%] h-[10vh] justify-between bg-[#1d1c1cff] border-[1px] border-[white] opacity-60 cursor-pointer"
                >
                    <p className="text-white font-thin">
                        {
                            value === ""
                                ?
                                "Select Category"
                                :
                                value
                        }
                    </p>

                    <ChevronsUpDown className="ml-2 h-4 w-6 text-white shrink-0 opacity-100" />
                </Button>
            </PopoverTrigger>

            <PopoverContent className="w-[100%] p-0 z-99999">
                <Command className="bg-[#1d1c1cff]">
                    <CommandInput className="text-black bg-[#1d1c1cff] h-full text-white font-thin" placeholder="Select Category" />
                    <CommandList>

                        <CommandGroup className="bg-[#1d1c1cff]">

                            {faqs.map((framework) => (
                                <CommandItem
                                    className="
                                        text-white font-thin
                                        data-[selected=true]:bg-[#1d1c1cff]
                                        data-[selected=true]:text-white
                                        hover:bg-[#2a2929]
                                        transition-colors
                                        cursor-pointer
                                    "
                                    key={framework.type}
                                    onSelect={(currentValue) => {
                                        setValue(
                                            currentValue === value
                                                ? value
                                                : currentValue
                                        )
                                        setOpen(false);
                                    }}
                                >

                                    <Check
                                        className={cn(
                                            "mr-2 h-4 w-4 font-white",
                                            value === framework.type ? "opacity-100" : "opacity-0"
                                        )}
                                    />
                                    {framework.type}
                                </CommandItem>
                            ))}

                        </CommandGroup>

                    </CommandList>
                </Command>
            </PopoverContent>
        </Popover>
    )
}
