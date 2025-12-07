import { useAuth } from "@/context/AuthContext";
import { transcribeAudio } from "@/lib/api/api";
import { RefObject, useRef } from "react";

export function useAudioWaves({ mediaRecorderRef, audioChunksRef, setInput, setFile, setLoading }
    : {
        mediaRecorderRef: RefObject<MediaRecorder | null>, audioChunksRef: RefObject<Blob[]>,
        setInput: (value: string) => void;
        setFile: (value: string) => void;
        setLoading: (value: boolean) => void;
    }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationRef = useRef<number>(0);
    const { user } = useAuth();

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            const audioCtx = new AudioContext();
            audioCtxRef.current = audioCtx;
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 1024;
            source.connect(analyser);

            analyserRef.current = analyser;
            sourceRef.current = source;

            const canvas = canvasRef.current!;
            const ctx = canvas.getContext("2d")!;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const drawBars = () => {
                animationRef.current = requestAnimationFrame(drawBars);
                analyser.getByteFrequencyData(dataArray);

                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const barWidth = 3;
                const barGap = 2;
                const centerY = canvas.height / 2;  //centers the waves
                const numBars = Math.floor(canvas.width / (barWidth + barGap));  // calculates numbers of bar those can be adjusted in canvas

                for (let i = 0; i < numBars; i++) {
                    const index = Math.floor((i / numBars) * bufferLength);
                    const value = dataArray[index];
                    const barHeight = (value / 255) * canvas.height * 1;

                    const x = i * (barWidth + barGap);
                    ctx.fillStyle = "#818181"; // gray tone like in your image
                    ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight);
                    ctx.beginPath();
                    ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 1.5);
                    ctx.fill();
                }
            };

            drawBars();

            mediaRecorder.ondataavailable = (event: BlobEvent) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                setFile(URL.createObjectURL(blob));

                const data = await transcribeAudio({ user, blob });
                setInput(data.text);
                setLoading(false);
                cancelAnimationFrame(animationRef.current!);
                analyser.disconnect();
                source.disconnect();
                audioCtx.close();
            };

            mediaRecorder.start();
        } catch (err) {
            console.error("Microphone access error:", err);
        }
    };
    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
    };

    return { stopRecording, startRecording, canvasRef };
}