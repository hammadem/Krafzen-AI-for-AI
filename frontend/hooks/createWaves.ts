import { RefObject, useRef } from "react";

export function useCreateWaves({
    mediaRecorderRef,
    canvasRef,
    setAudioURL,
    setIsRecording
}: {
    mediaRecorderRef: RefObject<MediaRecorder | null>;
    canvasRef: RefObject<HTMLCanvasElement | null>;
    setAudioURL: (value: string) => void;
    setIsRecording: (value: boolean) => void;
}) {
    const audioChunksRef = useRef<Blob[]>([]);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationRef = useRef<number>(0);

    const startRecording = async () => {
        setIsRecording(true);

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
                const centerY = canvas.height / 2;
                const numBars = Math.floor(canvas.width / (barWidth + barGap));

                for (let i = 0; i < numBars; i++) {
                    const index = Math.floor((i / numBars) * bufferLength);
                    const value = dataArray[index];
                    const barHeight = (value / 255) * canvas.height;

                    const x = i * (barWidth + barGap);
                    ctx.fillStyle = "#818181";
                    ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 1.5);
                    ctx.fill();
                }
            };

            drawBars();

            mediaRecorder.ondataavailable = (event: BlobEvent) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                const url = URL.createObjectURL(blob);
                setAudioURL(url);
                setIsRecording(false);

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
        setIsRecording(false);
    };

    return {
        startRecording,
        stopRecording
    };
}
