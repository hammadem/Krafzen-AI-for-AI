import { ChangeEvent } from "react";
import TextareaAutosize from "react-textarea-autosize"

export function InputGroupCustom({ input, setIsTwoLines, inputChange, user }: { user: User | null, input: string, setIsTwoLines: (val: boolean) => void, inputChange: (e: ChangeEvent<HTMLTextAreaElement>) => void }) {
    return (
        <div className="w-full rounded-md bg-background">
            <TextareaAutosize
                minRows={1}
                placeholder={"𝐂𝐡𝐚𝐭 or 𝐒𝐩𝐞𝐚𝐤 to draw"}
                onHeightChange={(height, { rowHeight }) => {
                    const rows = Math.round(height / rowHeight);
                    setIsTwoLines(rows >= 3);
                }}
                value={input}
                disabled={user === null}
                onChange={(e) => inputChange(e)}
                maxLength={500}
                className="
                    w-full
                    resize-none
                    bg-transparent
                    px-3
                    py-2.5
                    text-base
                    md:text-sm
                    leading-6

                    border-0
                    outline-none
                    ring-0
                    shadow-none

                    focus:outline-none
                    focus:ring-0
                    focus:shadow-none
                    max-h-[20vh]
                    custom-scrollbar1
                "
            />
        </div>
    )
} 