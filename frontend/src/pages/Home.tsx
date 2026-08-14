// frontend/src/pages/Home.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Sparkles, Zap } from 'lucide-react';
import { sendMessage, speakText } from '../services/api';

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
      text: '🔷 SYSTEM INITIALIZED\nSATURDAY AI v3.1 ONLINE\n\n🟣 AWAITING INPUT\n\n💡 Puedes decir: "dashboard", "proyectos" o "inicio" para navegar.',
      sender: 'saturday',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Detectar comandos de navegación
  const detectNavigation = (text: string): boolean => {
    const lower = text.toLowerCase().trim();
    
    if (lower === 'dashboard' || lower === 'ver dashboard' || lower === 'ir a dashboard') {
      if (onNavigate) onNavigate('dashboard');
      return true;
    }
    
    if (lower === 'proyectos' || lower === 'ver proyectos' || lower === 'ir a proyectos') {
      if (onNavigate) onNavigate('projects');
      return true;
    }
    
    if (lower === 'inicio' || lower === 'home' || lower === 'atrás' || lower === 'volver') {
      if (onNavigate) onNavigate('home');
      return true;
    }
    
    return false;
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: MessageType = {
      id: Date.now().toString(),
      text: input.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    
    const userText = input.trim();
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
            <button
              onClick={() => {
                setIsRecording(!isRecording);
                // Si se activa la grabación, simular entrada de voz
                if (!isRecording) {
                  // Aquí iría la lógica de reconocimiento de voz
                  // Por ahora, solo es visual
                }
              }}
              className={`icon-btn glass ${isRecording ? 'recording' : ''}`}
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
                placeholder={isRecording ? '🎤 ESCUCHANDO...' : 'Escribe un mensaje...'}
                className="composer__input"
                disabled={isLoading}
              />
            </div>

            <button
              onClick={handleSend}
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
                  setTimeout(handleSend, 100);
                }}
                className="suggestion-chip"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;