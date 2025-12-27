import { useAuth } from "@/context/AuthContext";
import { transcribeAudio } from "@/lib/api/api";
import { RefObject, useRef, useState } from "react";

export function useAudioWaves({
    mediaRecorderRef,
    audioChunksRef,
    setInput,
    setFile,
}: {
    mediaRecorderRef: RefObject<MediaRecorder | null>;
    audioChunksRef: RefObject<Blob[]>;
    setInput: (value: string) => void;
    setFile: (value: string) => void;
}) {
    const barsRef = useRef<SVGRectElement[]>([]);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationRef = useRef<number>(0);

    const { user } = useAuth();
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);


    const startRecording = async () => {
        try {
            setStatus("recording");
            setInput("");
            setFile("");

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            const audioCtx = new AudioContext();
            audioCtxRef.current = audioCtx;

            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 512;

            source.connect(analyser);

            analyserRef.current = analyser;
            sourceRef.current = source;

            const dataArray = new Uint8Array(analyser.frequencyBinCount);

            const animate = () => {
                animationRef.current = requestAnimationFrame(animate);
                analyser.getByteFrequencyData(dataArray);

                barsRef.current.forEach((bar, i) => {
                    const value = dataArray[i * 2] || 0;
                    const height = Math.max(4, (value / 255) * 30);
                    bar.setAttribute("height", height.toString());
                    bar.setAttribute("y", (35 - height).toString());
                });
            };

            animate();

            mediaRecorder.ondataavailable = (e) => {
                audioChunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                cancelAnimationFrame(animationRef.current);

                analyser.disconnect();
                source.disconnect();
                audioCtx.close();

                const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                setFile(URL.createObjectURL(blob));

                setStatus("parsingaudio");
                const { ok, data, error } = await transcribeAudio({ user, blob });

                if (ok) {
                    setInput((data as ParsedAudio).text);
                    setStatus("success");
                } else {
                    setStatus("error");
                    setApiError(error);
                }
            };

            mediaRecorder.start();
        } catch (err: unknown) {
            if (err instanceof Error) return {
                ok: false, data: null, error: {
                    type: "UNKNOWN",
                    message: err?.message
                }
            };
            else return {
                ok: false, data: null, error: {
                    type: "UNKNOWN",
                    message: "UNABLE TO ACCESS MICROPHONE"
                }
            };
        }
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
    };

    return { startRecording, stopRecording, barsRef, status, apiError };
}
