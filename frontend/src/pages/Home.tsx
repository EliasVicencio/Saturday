import { useState, useEffect, useRef, useCallback } from "react";
import {
  RefreshCw,
  Cloud,
  Camera as CameraIcon,
  Power,
  Clock,
  Maximize2,
  Send,
  Mic,
  MapPin,
  LayoutDashboard,
  Folder,
  Newspaper,
  ListTodo,
  CloudSun,
  Timer,
  Volume2,
  VolumeX,
} from "lucide-react";
import "../styles/Home.css";
import {
  sendMessage as apiSendMessage,
  getStatus,
  getWeather,
  type StatusResponse,
  type WeatherResponse,
} from "../services/api";

interface Message {
  id: string;
  sender: "saturday" | "user";
  text: string;
  time: string;
}

type NavKey = "dashboard" | "proyectos" | "noticias" | "tareas" | "clima" | "hora";

const formatTime = (d: Date) =>
  d.toLocaleTimeString("es-ES", { hour: "numeric", minute: "2-digit", second: "2-digit" });

const formatDate = (d: Date) =>
  d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });

const formatUptime = (seconds: number) => {
  const h = Math.floor(seconds / 3600).toString().padStart(2, "0");
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${h}:${m}:${s}`;
};

const navItems: { key: NavKey; label: string; icon: typeof LayoutDashboard }[] = [
  { key: "dashboard", label: "DASHBOARD", icon: LayoutDashboard },
  { key: "proyectos", label: "PROYECTOS", icon: Folder },
  { key: "noticias", label: "NOTICIAS", icon: Newspaper },
  { key: "tareas", label: "TAREAS", icon: ListTodo },
  { key: "clima", label: "CLIMA", icon: CloudSun },
  { key: "hora", label: "HORA", icon: Timer },
];

/** Logo: anillo tipo Saturno con núcleo brillante */
function SaturdayLogo({ pulsing }: { pulsing: boolean }) {
  return (
    <div className={`sd-logo-mark ${pulsing ? "sd-logo-mark--pulsing" : ""}`}>
      <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="sdLogoGrad" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <circle cx="20" cy="20" r="9" fill="url(#sdLogoGrad)" />
        <ellipse
          cx="20"
          cy="20"
          rx="18"
          ry="6.5"
          transform="rotate(-18 20 20)"
          stroke="url(#sdLogoGrad)"
          strokeWidth="1.6"
          opacity="0.85"
        />
        <ellipse
          cx="20"
          cy="20"
          rx="18"
          ry="6.5"
          transform="rotate(-18 20 20)"
          stroke="#0a1220"
          strokeWidth="4"
          strokeDasharray="0 34 8 100"
        />
      </svg>
    </div>
  );
}

/** Núcleo central: Saturno reinterpretado como átomo — 3 órbitas cruzadas en azul eléctrico */
function SaturnAtom({ active }: { active: boolean }) {
  return (
    <div className={`atom-wrap ${active ? "atom-wrap--active" : ""}`}>
      <div className="atom-glow" />
      <svg viewBox="0 0 240 240" className="atom-svg">
        <defs>
          <radialGradient id="atomCoreGrad" cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#e0f7ff" />
            <stop offset="35%" stopColor="#7dd8ff" />
            <stop offset="70%" stopColor="#1e90ff" />
            <stop offset="100%" stopColor="#0a3d91" />
          </radialGradient>
          <linearGradient id="atomRingGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>

        <g className="atom-orbit atom-orbit--1">
          <ellipse cx="120" cy="120" rx="105" ry="38" fill="none" stroke="url(#atomRingGrad)" strokeWidth="1.4" opacity="0.75" />
          <circle cx="225" cy="120" r="4.5" fill="#7ee6ff" className="atom-electron-glow" />
        </g>

        <g className="atom-orbit atom-orbit--2">
          <ellipse cx="120" cy="120" rx="105" ry="38" fill="none" stroke="url(#atomRingGrad)" strokeWidth="1.4" opacity="0.6" />
          <circle cx="225" cy="120" r="4" fill="#38bdf8" className="atom-electron-glow" />
        </g>

        <g className="atom-orbit atom-orbit--3">
          <ellipse cx="120" cy="120" rx="105" ry="38" fill="none" stroke="url(#atomRingGrad)" strokeWidth="1.4" opacity="0.6" />
          <circle cx="225" cy="120" r="4" fill="#93c5fd" className="atom-electron-glow" />
        </g>

        <circle cx="120" cy="120" r="34" fill="url(#atomCoreGrad)" className="atom-core" />
      </svg>
    </div>
  );
}

export default function Home() {
  const [now, setNow] = useState(new Date());
  const [uptime, setUptime] = useState(0);
  const [cameraOn, setCameraOn] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceOn, setVoiceOn] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [commandCount, setCommandCount] = useState(0);
  const [activeNav, setActiveNav] = useState<NavKey>("hora");
  const [sending, setSending] = useState(false);

  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [statusError, setStatusError] = useState(false);
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [floatingBubble, setFloatingBubble] = useState<{visible: boolean, text: string, icon: string} | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "saturday",
      text: "Hola, soy SATURDAY. Conectando con el backend...",
      time: formatTime(new Date()),
    },
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 1000);
    const up = setInterval(() => setUptime((u) => u + 1), 1000);
    return () => {
      clearInterval(clock);
      clearInterval(up);
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const refreshStatus = useCallback(async () => {
    try {
      const data = await getStatus();
      setStatus(data);
      setStatusError(false);
    } catch {
      setStatus(null);
      setStatusError(true);
    }
  }, []);

  const refreshWeather = useCallback(async () => {
    try {
      const data = await getWeather();
      setWeather(data);
    } catch {
      setWeather(null);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    refreshWeather();

    const statusInterval = setInterval(refreshStatus, 15000);
    const weatherInterval = setInterval(refreshWeather, 5 * 60 * 1000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(weatherInterval);
    };
  }, [refreshStatus, refreshWeather]);

  useEffect(() => {
    if (!status && !statusError) return;
    setMessages((prev) => {
      const greeting = statusError
        ? "No pude conectar con el backend. Revisá que esté corriendo en el puerto 5000, jefe."
        : `Backend conectado (v${status?.version ?? "?"}). ¿En qué te ayudo?`;
      if (prev.length === 1 && prev[0].id === "1") {
        return [{ ...prev[0], text: `Hola, soy SATURDAY. ${greeting}` }];
      }
      return prev;
    });
  }, [status, statusError]);

    const sendMessage = async (text?: string) => {
    const value = (text ?? inputValue).trim();
    if (!value || sending) return;

    const userMsg: Message = { id: Date.now().toString(), sender: "user", text: value, time: formatTime(new Date()) };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setCommandCount((c) => c + 1);
    setSending(true);

    try {
      const result = await apiSendMessage(value);
      const replyText = result.response || "No obtuve respuesta del backend.";
      
      // Verificar comandos especiales DESPUÉS de obtener la respuesta
      const isSystemInfo = value.toLowerCase().includes('estado del sistema');
      const isWeather = value.toLowerCase().includes('clima') || value.toLowerCase().includes('dime el clima');
      const isCamera = value.toLowerCase().includes('ver cámara') || value.toLowerCase().includes('cámara');
      
      if (isSystemInfo) {
        setFloatingBubble({ visible: true, text: replyText, icon: '⚙️' });
      } else if (isWeather) {
        setFloatingBubble({ visible: true, text: replyText, icon: '☀️' });
      } else if (isCamera) {
        setFloatingBubble({ 
          visible: true, 
          text: cameraOn ? '📷 Cámara activa' : '❌ Cámara no disponible', 
          icon: '📷' 
        });
      } else {
        setMessages((prev) => [
          ...prev,
          { id: (Date.now() + 1).toString(), sender: "saturday", text: replyText, time: formatTime(new Date()) }
        ]);
      }
      
      // Scroll al final
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
      
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "saturday",
          text: "⚠️ No pude comunicarme con el backend. Verificá que esté corriendo.",
          time: formatTime(new Date()),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const isOnline = !!status && status.status === "online";
  const activeModulesCount = status ? Object.values(status.modules).filter(Boolean).length : 0;

  return (
    <div className="sd">
      <div className="sd__bg-grid" />

      <header className="sd-topbar">
        <div className="sd-topbar__brand">
          <SaturdayLogo pulsing={listening} />
          <span className="sd-logo">SATURDAY</span>
          <span className={`pill ${isOnline ? "pill--online" : "pill--offline"}`}>
            <span className={`dot ${isOnline ? "dot--green" : "dot--gray"}`} />
            {isOnline ? "Online" : "Offline"}
          </span>
        </div>

        <div className="sd-topbar__center pill">
          <Clock size={14} />
          <span>{formatTime(now)}</span>
          <span className="topbar-sep">|</span>
          <span>{formatDate(now)}</span>
        </div>

        <div className="sd-topbar__right">
          <span className="pill">
            <MapPin size={13} />
            {weather ? `${weather.temp}°C` : "--°C"}{" "}
            <span className="muted">{weather?.city ?? "Sin datos"}</span>
          </span>
          <button
            className={`icon-square-btn ${voiceOn ? "icon-square-btn--active" : ""}`}
            onClick={() => setVoiceOn((v) => { setListening(!v); return !v; })}
            title={voiceOn ? "Voz activada" : "Voz desactivada"}
          >
            {voiceOn ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
        </div>
      </header>

      <div className="sd-main">
        <aside className="sd-sidebar">
          <section className="panel">
            <div className="panel__head">
              <div className="panel__title">
                <Cloud size={15} className="accent" />
                Weather
              </div>
              <button className="ghost-icon-btn" onClick={refreshWeather}>
                <RefreshCw size={13} />
              </button>
            </div>

            <div className="weather-main">
              <div>
                <div className="weather-temp">{weather ? `${weather.temp}°C` : "--°C"}</div>
                <div className="weather-loc">{weather ? `${weather.city}, ${weather.country}` : "Sin datos"}</div>
                <div className="weather-cond">{weather?.condition ?? "—"}</div>
              </div>
              <Cloud size={36} className="weather-icon" />
            </div>

            <div className="mini-stats mini-stats--3">
              <div className="mini-stat">
                <div className="mini-stat__label">Humidity</div>
                <div className="mini-stat__value">{weather ? `${weather.humidity}%` : "--"}</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Wind</div>
                <div className="mini-stat__value">{weather ? `${weather.wind} m/s` : "--"}</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Feels Like</div>
                <div className="mini-stat__value">{weather ? `${weather.feels_like}°C` : "--"}</div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <div className="panel__title">
                <CameraIcon size={15} className="accent" />
                Camera
              </div>
              <div className="panel__head-actions">
                <button className="ghost-icon-btn">
                  <CameraIcon size={13} />
                </button>
                <button
                  className={`ghost-icon-btn ${cameraOn ? "ghost-icon-btn--active" : ""}`}
                  onClick={() => setCameraOn((v) => !v)}
                >
                  <Power size={13} />
                </button>
              </div>
            </div>

            <div className="camera-view">
              {cameraOn ? (
                <div className="camera-view__live">LIVE FEED</div>
              ) : (
                <div className="camera-view__off">
                  <CameraIcon size={26} />
                  <span>Camera Off</span>
                </div>
              )}
            </div>
            <p className="camera-hint">
              {cameraOn ? "Camera is active." : "Camera is inactive. Click the power button to start."}
            </p>
          </section>

          <section className="panel">
            <div className="panel__head">
              <div className="panel__title">
                <Clock size={15} className="accent" />
                System Uptime
              </div>
              <div className="panel__head-actions">
                <span className="uptime-chip">{formatUptime(uptime)}</span>
                <button className="ghost-icon-btn">
                  <Maximize2 size={12} />
                </button>
              </div>
            </div>

            <div className="uptime-label">System Running For:</div>
            <div className="uptime-value">{formatUptime(uptime)}</div>

            <div className="mini-stats">
              <div className="mini-stat">
                <div className="mini-stat__label">Session</div>
                <div className="mini-stat__value">1</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Commands</div>
                <div className="mini-stat__value">{commandCount}</div>
              </div>
            </div>

            <div className="load-row">
              <div className="load-row__label">
                <span className="load-row__tag">{isOnline ? `${activeModulesCount} módulos activos` : "Sin conexión"}</span>
                <span>--%</span>
              </div>
              <div className="bar">
                <div className="bar__fill bar__fill--amber" style={{ width: "0%" }} />
              </div>
            </div>
          </section>
        </aside>

        <main className="sd-center">
          <SaturnAtom active={listening} />

          <button className="listening-pill" onClick={() => setVoiceOn((v) => { setListening(!v); return !v; })}>
            <Mic size={13} />
            {sending ? "SATURDAY PENSANDO..." : voiceOn ? "VOZ ACTIVADA" : "TOCA PARA ACTIVAR VOZ"}
          </button>

          <nav className="sd-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = activeNav === item.key;
              return (
                <button
                  key={item.key}
                  className={`sd-nav__item ${active ? "active" : ""}`}
                  onClick={() => setActiveNav(item.key)}
                >
                  <Icon size={14} />
                  {item.label}
                </button>
              );
            })}
          </nav>

          <div className="composer">
            <input
              type="text"
              placeholder="Escribe un mensaje o comando..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={sending}
            />
            <button className="composer__send" onClick={() => sendMessage()} disabled={sending || !inputValue.trim()}>
              <Send size={14} />
              {sending ? "Enviando..." : "Enviar"}
            </button>
          </div>
          
          {/* Burbuja flotante - Sistema */}
          {floatingBubble && floatingBubble.visible && (
            <div className="floating-bubble">
              <span className="floating-bubble__icon">{floatingBubble.icon}</span>
              <span className="floating-bubble__text">{floatingBubble.text}</span>
              <button 
                className="floating-bubble__close" 
                onClick={() => setFloatingBubble(null)}
              >
                ✕
              </button>
            </div>
          )}

          <div className="last-msg-preview">
            <span className="last-msg-preview__label">saturday:</span>
            <span className="last-msg-preview__dot" />
            {messages[messages.length - 1]?.text}
          </div>
        </main>
      </div>
    </div>
  );
}
