"use client";
import { ChangeEvent, useRef, useState } from "react";
import { useAudioWaves } from "@/hooks/useAudioWaves";
import { InputToolbar } from "./Toolbar/ToolbarComponents";
import { useCreateProject } from "@/hooks/useCreateProject";
import RecordingToolbar from "./Toolbar/RecordingToolbar";
import DrawingToolbar from "./Toolbar/PromptingToolbar";

export default function Toolbar() {
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    // Component state and requirements
    const [input, setInput] = useState<string>("");
    const [file, setFile] = useState<string>("");

    // Custom hooks
    const recordingState = useAudioWaves({ mediaRecorderRef, audioChunksRef, setInput, setFile });
    const projectReqState = useCreateProject();

    const inputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
        const prompt = e.target.value !== "" ? e.target.value : ""
        if (prompt && prompt !== "") setInput(prompt);
        else setInput("");
    }

    return (
        <>
            <RecordingToolbar
                canvasRef={recordingState.barsRef}
                stopRecording={recordingState.stopRecording}
                hidden={recordingState.status === "recording"}
            />
            <DrawingToolbar
                cancel={projectReqState.cancel}
                hidden={projectReqState.status === "prompting"}
            />
            <InputToolbar
                startRecording={recordingState.startRecording}
                inputChange={inputChange}
                input={input}
                setInput={setInput}
                createProject={projectReqState.createProject}
                file={file}
                setFile={setFile}
            />
        </>

    );
}
