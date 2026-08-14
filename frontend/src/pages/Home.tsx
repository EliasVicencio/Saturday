// frontend/src/pages/Home.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Sparkles, Zap } from 'lucide-react';
import { sendMessage, speakText, recognizeSpeech } from '../services/api';

interface MessageType {
  id: string;
  text: string;
  sender: 'user' | 'saturday';
  timestamp: Date;
}

interface HomeProps {
  onNavigate?: (view: 'home' | 'dashboard' | 'projects') => void;
}

const Home: React.FC<HomeProps> = ({ onNavigate }) => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: '1',
      text: '🔷 SYSTEM INITIALIZED\nSATURDAY AI v3.1 ONLINE\n\n🟣 AWAITING INPUT\n\n💡 Puedes decir: "dashboard", "proyectos" o "inicio" para navegar.\n🎤 Haz clic en el micrófono para hablar.',
      sender: 'saturday',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ===== RECONOCIMIENTO DE VOZ CON GOOGLE STT =====
  const startListening = async () => {
    // Verificar soporte del navegador para grabar audio
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('⚠️ Tu navegador no soporta grabación de audio.');
      return;
    }

    try {
      // Obtener acceso al micrófono
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
        } 
      });
      
      // Crear MediaRecorder
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        
        // Crear blob de audio en formato WAV
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        
        // Mostrar estado
        setInput('🔍 Reconociendo voz...');
        
        try {
          // Enviar a Google STT
          const text = await recognizeSpeech(audioBlob);
          
          // Detener el stream
          stream.getTracks().forEach(track => track.stop());
          
          if (text) {
            setInput(text);
            // Enviar automáticamente después de un breve delay
            setTimeout(() => {
              handleSend(text);
            }, 300);
          } else {
            setInput('');
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              text: '⚠️ No pude entender lo que dijiste. ¿Puedes repetirlo?',
              sender: 'saturday',
              timestamp: new Date(),
            }]);
          }
        } catch (error) {
          console.error('❌ Error procesando audio:', error);
          setInput('');
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            text: '⚠️ Error procesando el audio. Intenta de nuevo.',
            sender: 'saturday',
            timestamp: new Date(),
          }]);
        }
      };

      // Iniciar grabación
      mediaRecorder.start();
      setIsRecording(true);
      setInput('🎤 Escuchando...');
      
      // Guardar referencia para detener
      setRecognition({
        mediaRecorder,
        stream,
        stop: () => {
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          stream.getTracks().forEach(track => track.stop());
          setIsRecording(false);
          setInput('');
        }
      });

      // Detener automáticamente después de 10 segundos (límite de frase)
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
      }, 10000);

    } catch (error) {
      console.error('❌ Error accediendo al micrófono:', error);
      alert('⚠️ No se pudo acceder al micrófono. Verifica los permisos.');
    }
  };

  const stopListening = () => {
    if (recognition && recognition.stop) {
      recognition.stop();
    }
    setIsRecording(false);
    setInput('');
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopListening();
    } else {
      startListening();
    }
  };

  // ===== DETECTAR NAVEGACIÓN =====
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
    
    if (lower === 'inicio' || lower === 'home' || lower === 'atrás' || lower === 'volver') {
      if (onNavigate) onNavigate('home');
      return true;
    }
    
    return false;
  };

  // ===== ENVIAR MENSAJE =====
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

    // Verificar si es un comando de navegación
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
      
      // 👇 REPRODUCIR VOZ DE GOOGLE CHARON
      if (responseText) {
        await speakText(responseText);
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
    { label: '📋 Tareas', cmd: 'tareas' },
    { label: '🌤️ Clima', cmd: 'clima' },
    { label: '🕐 Hora', cmd: 'hora' },
  ];

  return (
    <div className="page">
      <div className="ambient-bg">
        <div
          className="ambient-glow"
          style={{ top: '20%', left: '20%', width: 400, height: 400, background: 'rgba(37,99,235,0.06)' }}
        />
        <div
          className="ambient-glow"
          style={{ bottom: '20%', right: '20%', width: 300, height: 300, background: 'rgba(6,182,212,0.06)', animationDelay: '1s' }}
        />
        <div className="ambient-scan animate-scan" />
      </div>

      <header className="page-header">
        <div className="page-header__title">
          <div style={{ position: 'relative' }}>
            <div
              className="animate-pulse-ring"
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(37,99,235,0.2), rgba(6,182,212,0.2))',
                border: '1px solid rgba(96,165,250,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Sparkles size={18} color="#22d3ee" />
            </div>
            <span
              className="animate-pulse-soft"
              style={{
                position: 'absolute',
                bottom: -1,
                right: -1,
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: '#22d3ee',
              }}
            />
          </div>
          <div>
            <h1 className="gradient-text">SATURDAY</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 2 }}>
              <span style={{ fontSize: 8, color: 'rgba(147,197,253,0.5)', letterSpacing: '0.1em' }}>
                AI ASSISTANT · v3.1
              </span>
              <span className="status-pill__divider" style={{ width: 1, height: 12, background: 'rgba(37,99,235,0.2)' }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 8, color: 'rgba(34,211,238,0.6)' }}>
                <span className="status-dot animate-pulse-soft" />
                <span>ONLINE</span>
              </div>
            </div>
          </div>
        </div>
        <div className="badge badge-blue">
          <Zap size={12} color="#22d3ee" />
          <span>12ms</span>
        </div>
      </header>

      <div className="chat-scroll">
        <div className="chat-scroll__inner">
          {messages.map((msg) => (
            <div key={msg.id} className={`chat-row ${msg.sender === 'user' ? 'user' : 'bot'} fade-in`}>
              <div className={`chat-bubble-wrap ${msg.sender === 'user' ? 'user' : ''}`}>
                {msg.sender === 'saturday' && (
                  <div className="chat-prompt-line">
                    <span>SATURDAY@CORE:~$</span>
                    <span className="chat-caret animate-pulse-soft" />
                  </div>
                )}
                <div className={`chat-bubble glass ${msg.sender === 'user' ? 'user' : 'bot'}`}>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  <div className="chat-time">
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

      <div className="composer">
        <div className="composer__inner">
          <div className="composer__row">
            {/* 👇 BOTÓN DE MICRÓFONO CON RECONOCIMIENTO DE VOZ */}
            <button
              onClick={toggleRecording}
              className={`icon-btn glass ${isRecording ? 'recording' : ''}`}
              title={isRecording ? 'Detener grabación' : 'Hablar con Saturday'}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            <div className="composer__input-wrap">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isRecording ? '🎤 ESCUCHANDO...' : 'Escribe o habla...'}
                className="composer__input"
                disabled={isLoading}
              />
              {isRecording && (
                <div className="recording-indicator">
                  <span className="recording-dot animate-pulse-soft" />
                  <span className="recording-text">Grabando...</span>
                </div>
              )}
            </div>

            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="icon-btn gradient-btn"
            >
              <Send size={18} />
            </button>
          </div>

          <div className="suggestions">
            {suggestions.map((item, i) => (
              <button
                key={i}
                onClick={() => {
                  setInput(item.cmd);
                  setTimeout(() => handleSend(), 100);
                }}
                className="suggestion-chip"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        .recording-indicator {
          position: absolute;
          right: 12px;
          top: 50%;
          transform: translateY(-50%);
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(239, 68, 68, 0.1);
          padding: 4px 12px;
          border-radius: 9999px;
          border: 1px solid rgba(239, 68, 68, 0.2);
          pointer-events: none;
        }
        .recording-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #ef4444;
        }
        .recording-text {
          font-size: 8px;
          color: #ef4444;
          font-family: 'JetBrains Mono', monospace;
        }
      `}</style>
    </div>
  );
};

export default Home;