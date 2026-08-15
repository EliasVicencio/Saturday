// frontend/src/pages/Home.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Sparkles, Zap } from 'lucide-react';
import { sendMessage, speakText } from '../services/api';
import '../styles/Home.css';

interface MessageType {
  id: string;
  text: string;
  sender: 'user' | 'saturday';
  timestamp: Date;
}

interface HomeProps {
  onNavigate?: (view: 'home' | 'dashboard' | 'projects' | 'news') => void;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

const Home: React.FC<HomeProps> = ({ onNavigate }) => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: '1',
      text: '🔷 SYSTEM INITIALIZED\nSATURDAY AI v3.1 ONLINE\n\n🟣 AWAITING INPUT\n\n💡 Puedes decir: "dashboard", "proyectos", "noticias" o "inicio" para navegar.\n🎤 Haz clic en el micrófono y habla (se detendrá automáticamente).',
      sender: 'saturday',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSaturdaySpeaking, setIsSaturdaySpeaking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const speakTextWithIndicator = async (text: string) => {
    setIsSaturdaySpeaking(true);
    try {
      await speakText(text);
    } finally {
      setIsSaturdaySpeaking(false);
    }
  };

  const startRecording = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('⚠️ Tu navegador no soporta grabación de audio.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      audioChunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;
      streamRef.current = stream;

      let audioContext: AudioContext | null = null;
      let analyser: AnalyserNode | null = null;
      let silenceStartTime: number | null = null;
      const SILENCE_THRESHOLD = 0.01;
      const SILENCE_DURATION = 1500;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstart = () => {
        setIsRecording(true);
        setIsProcessing(false);
        setTranscript('🎤 Escuchando...');
        silenceStartTime = null;

        try {
          audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const source = audioContext.createMediaStreamSource(stream);
          analyser = audioContext.createAnalyser();
          analyser.fftSize = 512;
          source.connect(analyser);

          const dataArray = new Uint8Array(analyser.frequencyBinCount);

          const checkSilence = () => {
            if (!analyser || !mediaRecorder || mediaRecorder.state !== 'recording') return;
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const average = sum / dataArray.length;
            const normalized = average / 255;

            if (normalized < SILENCE_THRESHOLD) {
              if (silenceStartTime === null) {
                silenceStartTime = Date.now();
              } else if (Date.now() - silenceStartTime > SILENCE_DURATION) {
                console.log('🔇 Silencio detectado, deteniendo grabación...');
                if (mediaRecorder.state === 'recording') {
                  mediaRecorder.stop();
                }
                return;
              }
            } else {
              silenceStartTime = null;
            }
            requestAnimationFrame(checkSilence);
          };
          checkSilence();
        } catch (error) {
          console.warn('⚠️ No se pudo detectar silencio:', error);
          setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
              mediaRecorder.stop();
            }
          }, 10000);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        setIsProcessing(true);
        setTranscript('🔍 Procesando...');

        if (audioContext) {
          try {
            await audioContext.close();
          } catch (e) {}
        }

        if (audioChunksRef.current.length === 0) {
          setTranscript('');
          setIsProcessing(false);
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
        }

        if (audioBlob.size < 1000) {
          setTranscript('⚠️ No detecté voz');
          setTimeout(() => {
            setTranscript('');
            setIsProcessing(false);
          }, 1500);
          return;
        }

        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          const response = await fetch('http://localhost:5000/api/stt', {
            method: 'POST',
            body: formData,
          });
          const data = await response.json();

          if (data.success && data.text) {
            setTranscript(`"${data.text}"`);
            setTimeout(() => {
              setTranscript('');
              setIsProcessing(false);
              handleSend(data.text);
            }, 500);
          } else {
            setTranscript('⚠️ No entendí');
            setTimeout(() => {
              setTranscript('');
              setIsProcessing(false);
            }, 1500);
          }
        } catch (error) {
          console.error('❌ Error procesando audio:', error);
          setTranscript('⚠️ Error');
          setIsProcessing(false);
          setTimeout(() => setTranscript(''), 1500);
        }
      };

      mediaRecorder.start();
      setRecognition({
        mediaRecorder,
        stream,
        stop: () => {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          if (stream) {
            stream.getTracks().forEach((track) => track.stop());
          }
          setIsRecording(false);
          setIsProcessing(false);
          setTranscript('');
        },
      });
    } catch (error) {
      console.error('❌ Error accediendo al micrófono:', error);
      alert('⚠️ No se pudo acceder al micrófono. Verifica los permisos.');
    }
  };

  const stopRecording = () => {
    if (recognition && recognition.stop) {
      recognition.stop();
    }
    setIsRecording(false);
    setIsProcessing(false);
    setTranscript('');
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const detectNavigation = (text: string): boolean => {
    const lower = text.toLowerCase().trim();
    if (lower === 'dashboard' || lower === 'ver dashboard' || lower === 'ir a dashboard') {
      if (onNavigate) onNavigate('dashboard');
      return true;
    }
    if (lower === 'proyectos' || lower === 'ver proyectos' || lower === 'ir a proyectos' || lower === 'projects') {
      if (onNavigate) onNavigate('projects');
      return true;
    }
    if (lower === 'noticias' || lower === 'ver noticias' || lower === 'ir a noticias' || lower === 'news') {
      if (onNavigate) onNavigate('news');
      return true;
    }
    if (lower === 'inicio' || lower === 'home' || lower === 'atrás' || lower === 'volver') {
      if (onNavigate) onNavigate('home');
      return true;
    }
    return false;
  };

  const handleSend = async (text?: string) => {
    const messageToSend = text || input;
    if (!messageToSend.trim() || isLoading) return;

    const userMessage: MessageType = {
      id: Date.now().toString(),
      text: messageToSend.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const userText = messageToSend.trim();
    setInput('');
    setIsLoading(true);

    if (detectNavigation(userText)) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await sendMessage(userText);
      const responseText = response.response || 'ERROR: COMMAND NOT RECOGNIZED';
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: responseText,
          sender: 'saturday',
          timestamp: new Date(),
        },
      ]);
      if (responseText) {
        await speakTextWithIndicator(responseText);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: '⚠️ CONNECTION ERROR',
          sender: 'saturday',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    { label: '📊 Dashboard', cmd: 'dashboard' },
    { label: '📁 Proyectos', cmd: 'proyectos' },
    { label: '📰 Noticias', cmd: 'noticias' },
    { label: '📋 Tareas', cmd: 'tareas' },
    { label: '🌤️ Clima', cmd: 'clima' },
    { label: '🕐 Hora', cmd: 'hora' },
  ];

  const getHologramState = () => {
    if (isSaturdaySpeaking) return 'active';
    if (isRecording) return 'recording';
    if (isProcessing) return 'processing';
    return 'idle';
  };

  const hologramState = getHologramState();

  return (
    <div className="page">
      <div className="ambient-bg">
        <div className="ambient-glow" style={{ top: '20%', left: '20%', width: 400, height: 400, background: 'rgba(37,99,235,0.06)' }} />
        <div className="ambient-glow" style={{ bottom: '20%', right: '20%', width: 300, height: 300, background: 'rgba(6,182,212,0.06)', animationDelay: '1s' }} />
      </div>

      <header className="page-header">
        <div className="page-header__title">
          <div style={{ position: 'relative' }}>
            <div className="animate-pulse-ring" style={{ width: 40, height: 40, borderRadius: '50%', background: 'linear-gradient(135deg, rgba(37,99,235,0.2), rgba(6,182,212,0.2))', border: '1px solid rgba(96,165,250,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Sparkles size={18} color="#22d3ee" />
            </div>
            <span className="animate-pulse-soft" style={{ position: 'absolute', bottom: -1, right: -1, width: 8, height: 8, borderRadius: '50%', background: '#22d3ee' }} />
          </div>
          <div>
            <h1 className="gradient-text" style={{ fontSize: 24 }}>SATURDAY</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 2 }}>
              <span style={{ fontSize: 10, color: 'rgba(147,197,253,0.5)', letterSpacing: '0.1em' }}>AI ASSISTANT · v3.1</span>
              <span className="status-pill__divider" style={{ width: 1, height: 12, background: 'rgba(37,99,235,0.2)' }} />
              <span style={{ fontSize: 9, color: '#22d3ee' }}>● ONLINE</span>
            </div>
          </div>
        </div>
      </header>

      <div className="main-content">
        <div className={`hologram-container ${hologramState}`} data-state={hologramState}>
          <div className="hologram-base">
            <div className="hologram-ring ring-1" />
            <div className="hologram-ring ring-2" />
            <div className="hologram-ring ring-3" />
          </div>
          <div className="hologram-scan"><div className="scan-line" /></div>
          <div className="hologram-particles">
            <div className="particle p1" /><div className="particle p2" />
            <div className="particle p3" /><div className="particle p4" />
            <div className="particle p5" /><div className="particle p6" />
            <div className="particle p7" /><div className="particle p8" />
          </div>
          <div className="hologram-core">
            <button onClick={toggleRecording} className="hologram-button" disabled={isLoading || isProcessing || isSaturdaySpeaking}>
              {isRecording ? <MicOff size={36} color="#ef4444" /> : isProcessing ? <span style={{ fontSize: 28, color: '#f59e0b' }}>⏳</span> : <Mic size={36} color="#22d3ee" />}
            </button>
          </div>
          <div className="hologram-text">
            {isSaturdaySpeaking && <span className="holo-text speaking">🔊 SATURDAY HABLANDO</span>}
            {isRecording && <span className="holo-text listening">🎤 ESCUCHANDO...</span>}
            {isProcessing && <span className="holo-text processing">⏳ PROCESANDO...</span>}
            {!isRecording && !isProcessing && !isSaturdaySpeaking && <span className="holo-text idle">🎙️ TOCA PARA HABLAR</span>}
          </div>
          <div className="hologram-distortion" />
        </div>
        {transcript && (
          <div className="transcript-display">
            <span className="transcript-text">{transcript}</span>
          </div>
        )}
      </div>

      <div className="composer">
        <div className="composer__inner">
          <div className="composer__row">
            <input ref={inputRef} type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Escribe un mensaje..." className="composer__input" disabled={isLoading} />
            <button onClick={() => handleSend()} disabled={isLoading || !input.trim()} className="icon-btn gradient-btn"><Send size={18} /></button>
          </div>
          <div className="suggestions">
            {suggestions.map((item) => (
              <button key={item.cmd} onClick={() => { setInput(item.cmd); setTimeout(() => handleSend(), 100); }} className="suggestion-chip">{item.label}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-scroll">
          <div className="chat-scroll__inner">
            {messages.slice(-4).map((msg) => (
              <div key={msg.id} className={`chat-row ${msg.sender === 'user' ? 'user' : 'bot'} fade-in`}>
                <div className={`chat-bubble-wrap ${msg.sender === 'user' ? 'user' : ''}`}>
                  {msg.sender === 'saturday' && (
                    <div className="chat-prompt-line">
                      <span>SATURDAY@CORE:~$</span>
                      <span className="chat-caret animate-pulse-soft" />
                    </div>
                  )}
                  <div className={`chat-bubble glass ${msg.sender === 'user' ? 'user' : 'bot'}`}>
                    <div className="whitespace-pre-wrap" style={{ fontSize: 12 }}>{msg.text}</div>
                    <div className="chat-time" style={{ fontSize: 8 }}>
                      {msg.timestamp.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="typing-row">
                <span className="typing-dot animate-bounce-dot" />
                <span className="typing-dot animate-bounce-dot" style={{ animationDelay: '0.15s' }} />
                <span className="typing-dot animate-bounce-dot" style={{ animationDelay: '0.3s' }} />
                <span className="typing-label">PROCESSING...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;