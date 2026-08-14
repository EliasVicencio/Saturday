// frontend/src/pages/Home.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Sparkles, Zap, Circle } from 'lucide-react';
import { sendMessage } from '../services/api';

interface MessageType {
  id: string;
  text: string;
  sender: 'user' | 'saturday';
  timestamp: Date;
}

const Home: React.FC = () => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: '1',
      text: '🔷 SYSTEM INITIALIZED\nSATURDAY AI v3.1 ONLINE\n\n🟣 AWAITING INPUT',
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
    if (inputRef.current) inputRef.current.focus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: MessageType = {
      id: Date.now().toString(),
      text: input.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage.text);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: response.response || 'ERROR: COMMAND NOT RECOGNIZED',
        sender: 'saturday',
        timestamp: new Date(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: '⚠️ CONNECTION ERROR',
        sender: 'saturday',
        timestamp: new Date(),
      }]);
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

  return (
    <div className="w-full h-full bg-[#0a0e1a] text-white flex flex-col overflow-hidden relative">
      {/* ===== FONDO CON PARTÍCULAS ===== */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-cyan-500/5" />
        <div className="absolute top-1/4 left-1/4 w-[400px] h-[400px] rounded-full bg-blue-500/[0.04] blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] rounded-full bg-cyan-500/[0.04] blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-gradient-to-r from-blue-500/[0.02] to-cyan-500/[0.02] blur-3xl" />
        {/* Línea de escaneo */}
        <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(37,99,235,0.02)_50%)] bg-[length:100%_4px] animate-scan" />
      </div>

      {/* ===== HEADER CON BRILLO ===== */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4 border-b border-blue-500/20 bg-[#0a0e1a]/80 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-400/30 flex items-center justify-center animate-pulse-ring">
              <Sparkles className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="text-xl font-bold gradient-text tracking-[0.3em]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
              SATURDAY
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[8px] text-blue-300/50 tracking-[0.15em]">AI ASSISTANT · v3.1</span>
              <span className="w-px h-3 bg-blue-500/20" />
              <div className="flex items-center gap-1.5 text-[8px] text-cyan-400/60">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
                <span>ONLINE</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <Zap className="w-3 h-3 text-cyan-400" />
            <span className="text-[8px] text-blue-300/50 font-mono">12ms</span>
          </div>
        </div>
      </header>

      {/* ===== CHAT ===== */}
      <div className="relative z-10 flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg, index) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-[fadeIn_0.3s_ease-out]`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className={`max-w-[80%] ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                  {msg.sender === 'saturday' && (
                    <div className="text-[7px] text-blue-400/30 mb-0.5 font-mono flex items-center gap-2">
                      <span>SATURDAY@CORE:~$</span>
                      <span className="w-1 h-3 bg-blue-400/30 animate-pulse inline-block" />
                    </div>
                  )}
                  <div className={`relative p-3 rounded-2xl ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-400/20 text-cyan-400'
                      : 'glass text-blue-200/70'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap font-mono">
                      {msg.text}
                    </div>
                    <div className="text-[6px] text-blue-400/20 mt-1 font-mono">
                      {msg.timestamp.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 px-4 py-2">
                <span className="w-2 h-2 rounded-full bg-blue-400/40 animate-bounce" />
                <span className="w-2 h-2 rounded-full bg-blue-400/40 animate-bounce" style={{ animationDelay: '0.15s' }} />
                <span className="w-2 h-2 rounded-full bg-blue-400/40 animate-bounce" style={{ animationDelay: '0.3s' }} />
                <span className="text-[7px] text-blue-400/30 ml-2 font-mono">PROCESSING...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* ===== INPUT CON EFECTO ===== */}
        <div className="border-t border-blue-500/20 bg-[#0a0e1a]/95 backdrop-blur-sm flex-shrink-0 px-6 py-5">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`p-3.5 rounded-full transition-all ${
                  isRecording
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse'
                    : 'glass text-blue-400/60 hover:text-cyan-400 hover:border-cyan-400/30'
                }`}
              >
                {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <div className="flex-1 relative">
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/5 to-cyan-500/5 blur-sm pointer-events-none" />
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isRecording ? '🎤 ESCUCHANDO...' : 'Escribe un mensaje...'}
                  className="w-full bg-blue-500/5 border border-blue-400/20 rounded-xl px-5 py-3.5 text-sm font-mono text-blue-200/80 placeholder-blue-400/25 focus:outline-none focus:border-cyan-400/50 focus:ring-1 focus:ring-cyan-400/20 transition-all relative z-10"
                  disabled={isLoading}
                />
                {!isLoading && !input && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 z-10">
                    <span className="text-[8px] text-blue-400/20 font-mono animate-pulse">▍</span>
                  </div>
                )}
              </div>

              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="p-3.5 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-[0_0_40px_rgba(37,99,235,0.2)] hover:shadow-[0_0_60px_rgba(37,99,235,0.3)]"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>

            {/* ===== SUGERENCIAS ===== */}
            <div className="flex justify-center gap-3 mt-4 flex-wrap">
              {['📋 Tareas', '📝 Nota', '📅 Evento', '🌤️ Clima', '🕐 Hora'].map((label, i) => (
                <button
                  key={i}
                  onClick={() => {
                    const cmd = label.split(' ')[1].toLowerCase();
                    setInput(cmd);
                    setTimeout(handleSend, 100);
                  }}
                  className="px-3 py-1.5 rounded-full text-[8px] font-mono bg-blue-500/10 border border-blue-500/20 text-blue-400/50 hover:text-cyan-400 hover:border-cyan-400/30 transition-all"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;