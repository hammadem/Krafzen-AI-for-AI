import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SearchIcon } from "lucide-react";
import { TemplateBox } from "./Examples";

export default function Templates() {
    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Templates</h1>

                <p className="text-[#8F8F8F]">Browse and start your project with a pre-designed template.</p>

                <span className="flex gap-4 text-[#8F8F8F]">
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border-1 border-[#8F8F8F] rounded-[10px] w-full focus-within:none transition">
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
                                <SelectLabel>Fruits</SelectLabel>
                                <SelectItem value="apple">Apple</SelectItem>
                                <SelectItem value="banana">Banana</SelectItem>
                                <SelectItem value="blueberry">Blueberry</SelectItem>
                                <SelectItem value="grapes">Grapes</SelectItem>
                                <SelectItem value="pineapple">Pineapple</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>

                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="outline" className="hover:bg-[#0F0F0F] bg-[#0F0F0F] hover:text-[#8F8F8F] border-1 border-[#8F8F8F] flex gap-2 items-center font-semibold justify-center">
                                <div className="w-10 flex h-[80%] gap-1 flex-col items-center justify-center">
                                    <span className="w-[72%] h-[18%] bg-[#8F8F8F]"></span>
                                    <span className="w-[48%] h-[18%] bg-[#8F8F8F]"></span>
                                    <span className="w-[24%] h-[18%] bg-[#8F8F8F]"></span>
                                </div>
                                Filter
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-80">
                            <div className="grid gap-4">
                                <div className="space-y-2">
                                    <h4 className="leading-none font-medium">Dimensions</h4>
                                    <p className="text-muted-foreground text-sm">
                                        Set the dimensions for the layer.
                                    </p>
                                </div>
                                <div className="grid gap-2">
                                    <div className="grid grid-cols-3 items-center gap-4">
                                        <Label htmlFor="width">Width</Label>
                                        <Input
                                            id="width"
                                            defaultValue="100%"
                                            className="col-span-2 h-8"
                                        />
                                    </div>
                                    <div className="grid grid-cols-3 items-center gap-4">
                                        <Label htmlFor="maxWidth">Max. width</Label>
                                        <Input
                                            id="maxWidth"
                                            defaultValue="300px"
                                            className="col-span-2 h-8"
                                        />
                                    </div>
                                    <div className="grid grid-cols-3 items-center gap-4">
                                        <Label htmlFor="height">Height</Label>
                                        <Input
                                            id="height"
                                            defaultValue="25px"
                                            className="col-span-2 h-8"
                                        />
                                    </div>
                                    <div className="grid grid-cols-3 items-center gap-4">
                                        <Label htmlFor="maxHeight">Max. height</Label>
                                        <Input
                                            id="maxHeight"
                                            defaultValue="none"
                                            className="col-span-2 h-8"
                                        />
                                    </div>
                                </div>
                            </div>
                        </PopoverContent>
                    </Popover>

                </span>

                <div className="grid grid-cols-4 gap-4">
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                    <TemplateBox />
                </div>

            </div>
        </div>
    )
}