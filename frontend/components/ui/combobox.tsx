"use client";
import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
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
import { faqs } from "@/lib/data";

export function ComboboxDemo({ setValue, value }: { setValue: React.Dispatch<React.SetStateAction<string>>, value: string }) {
    const [open, setOpen] = React.useState(false);

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="secondary"
                    role="combobox"
                    aria-expanded={open}
                    className="w-[90%] h-[10vh] justify-between bg-[#1d1c1cff] border-[1px] border-white opacity-90 cursor-pointer"
                >
                    <p className="text-white text-xl font-normal">
                        {
                            value === ""
                                ?
                                "Select Category"
                                :
                                value
                        }
                    </p>

                    <ChevronsUpDown className="ml-2 h-6 w-8 text-white shrink-0 opacity-100" />
                </Button>
            </PopoverTrigger>

            <PopoverContent className="
            w-[80%]
            mx-auto bg-[#1d1c1cff] z-99999 border-2"
            >
                <Command className="bg-[#1d1c1cff] text-white">

                    <div className="py-2 w-full">
                        <CommandInput className="text-3xl bg-[#1d1c1cff] h-[15vh] w-full text-white font-thin" placeholder="Select Category" />
                    </div>

                    <CommandList className="w-full mx-auto">
                        <CommandGroup className="bg-[#1d1c1cff]">

                            {faqs.map((framework) => (
                                <CommandItem
                                    className="
                                        text-white font-normal text-xl
                                        data-[selected=true]:bg-[#1d1c1cff]
                                        data-[selected=true]:text-white
                                        hover:bg-[#2a2929]
                                        transition-colors
                                        cursor-pointer
                                        h-[7vh]
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
                                            "mr-2 h-4 w-4 text-white",
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
        </Popover >
    )
}
