import { useCallback, useRef, useState } from "react";
import { recognizeSpeech } from "../services/api";

interface UseSpeechRecognitionOptions {
  lang?: string;
  onFinalResult?: (transcript: string) => void;
}

export function useSpeechRecognition({ onFinalResult }: UseSpeechRecognitionOptions = {}) {
  const [listening, setListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onFinalResultRef = useRef(onFinalResult);
  onFinalResultRef.current = onFinalResult;

  const start = useCallback(async () => {
    setError(null);
    setInterimTranscript("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;

      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;

        const blob = new Blob(chunks, { type: "audio/webm" });
        setInterimTranscript("Procesando audio...");

        try {
          const text = await recognizeSpeech(blob);
          setInterimTranscript("");
          if (text) {
            onFinalResultRef.current?.(text);
          } else {
            setError("No se reconoció voz");
          }
        } catch {
          setInterimTranscript("");
          setError("Error al procesar audio");
        }
      };

      recorder.start();
      setListening(true);
    } catch {
      setError("No se pudo acceder al micrófono");
      setListening(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { supported: true, listening, interimTranscript, error, start, stop, toggle };
}
