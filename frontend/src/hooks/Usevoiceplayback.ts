import { useCallback, useEffect, useRef, useState } from "react";
import { synthesizeSpeech } from "../services/api";

interface UseVoicePlaybackReturn {
  /** true mientras el audio de Saturday está sonando */
  speaking: boolean;
  /** amplitud del audio en el instante actual, 0..1 (para animar en vivo) */
  level: number;
  /** reproduce el texto en voz, analizando su amplitud en tiempo real */
  speak: (text: string) => Promise<void>;
  /** corta el audio en seco (ej: el usuario apaga la voz o manda otro mensaje) */
  stop: () => void;
}

/**
 * Reproduce la respuesta de Saturday en voz alta y analiza la amplitud real
 * del audio con un AnalyserNode (Web Audio API), frame a frame, para que
 * cualquier visual (la esfera de partículas) pueda "reaccionar" de verdad
 * al sonido de la voz en vez de solo prender/apagar un estado fijo.
 */
export function useVoicePlayback(): UseVoicePlaybackReturn {
  const [speaking, setSpeaking] = useState(false);
  const [level, setLevel] = useState(0);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      audioCtxRef.current = new Ctor();
    }
    return audioCtxRef.current;
  }, []);

  const tick = useCallback(() => {
    const analyser = analyserRef.current;
    const dataArray = dataArrayRef.current;
    if (!analyser || !dataArray) return;

    analyser.getByteTimeDomainData(dataArray);
    // RMS de la forma de onda: qué tan lejos del silencio (128) está la señal
    let sumSquares = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const norm = (dataArray[i] - 128) / 128;
      sumSquares += norm * norm;
    }
    const rms = Math.sqrt(sumSquares / dataArray.length);
    setLevel(Math.min(1, rms * 3.2)); // ganancia para que se note en pantalla

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const stop = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    setSpeaking(false);
    setLevel(0);
  }, []);

  const speak = useCallback(
    async (text: string) => {
      stop(); // corta cualquier audio anterior que siga sonando

      const audio = await synthesizeSpeech(text);
      if (!audio) return;

      currentAudioRef.current = audio;

      try {
        const ctx = getAudioContext();
        if (ctx.state === "suspended") await ctx.resume();

        const source = ctx.createMediaElementSource(audio);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyser.connect(ctx.destination);

        analyserRef.current = analyser;
        dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
      } catch (err) {
        // si Web Audio no está disponible o falla el análisis, el audio
        // igual se reproduce normal, solo sin animación reactiva
        console.warn("No se pudo analizar el audio en tiempo real:", err);
      }

      audio.onended = () => {
        setSpeaking(false);
        setLevel(0);
        if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
        currentAudioRef.current = null;
      };
      audio.onerror = () => {
        setSpeaking(false);
        setLevel(0);
        if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      };

      try {
        await audio.play();
        setSpeaking(true);
        rafRef.current = requestAnimationFrame(tick);
      } catch (err) {
        console.warn("No se pudo reproducir la voz:", err);
        setSpeaking(false);
      }
    },
    [getAudioContext, stop, tick]
  );

  useEffect(() => {
    return () => {
      stop();
      audioCtxRef.current?.close().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { speaking, level, speak, stop };
}