import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Tipado mínimo de la Web Speech API (SpeechRecognition), que no viene
 * incluido en las libs estándar de TypeScript/DOM.
 */
interface SpeechRecognitionResultLike {
  isFinal: boolean;
  0: { transcript: string };
}
interface SpeechRecognitionEventLike extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultLike[];
}
interface SpeechRecognitionErrorEventLike extends Event {
  error: string;
}
interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
}
type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

function getSpeechRecognitionCtor(): SpeechRecognitionConstructor | null {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

interface UseSpeechRecognitionOptions {
  lang?: string;
  /** se llama con el texto final apenas el usuario termina de hablar */
  onFinalResult?: (transcript: string) => void;
}

export function useSpeechRecognition({ lang = "es-CL", onFinalResult }: UseSpeechRecognitionOptions = {}) {
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const onFinalResultRef = useRef(onFinalResult);
  onFinalResultRef.current = onFinalResult;

  useEffect(() => {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      setSupported(false);
      return;
    }

    const recognition = new Ctor();
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }
      if (final.trim()) {
        setInterimTranscript("");
        onFinalResultRef.current?.(final.trim());
      } else {
        setInterimTranscript(interim);
      }
    };

    recognition.onerror = (event) => {
      // "no-speech" pasa seguido si el usuario no dijo nada a tiempo; no es un error real
      if (event.error !== "no-speech") {
        setError(event.error);
      }
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
      setInterimTranscript("");
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      recognition.abort();
    };
  }, [lang]);

  const start = useCallback(() => {
    if (!recognitionRef.current) return;
    setError(null);
    setInterimTranscript("");
    try {
      recognitionRef.current.start();
      setListening(true);
    } catch {
      // ya estaba corriendo (el navegador tira excepción si se llama 2 veces seguidas)
    }
  }, []);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) stop();
    else start();
  }, [listening, start, stop]);

  return { supported, listening, interimTranscript, error, start, stop, toggle };
}