import { useState, useEffect, useRef, useCallback } from "react";
import {
  Send,
  Mic,
  MicOff,
  Cpu,
  Users,
  MessageSquare,
  ListChecks,
  Percent,
  ChevronRight,
  Lock,
  MapPin,
} from "lucide-react";
import "../styles/Home.css";
import VaultGraph from "../components/Vaultgraph";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import {
  sendMessage as apiSendMessage,
  speakText,
  getStatus,
  getWeather,
  getSystemStats,
  getVaultStats,
  getVaultNotes,
  getTasksList,
  getEventsToday,
  type StatusResponse,
  type WeatherResponse,
  type SystemStats,
  type VaultStats,
  type VaultNote,
  type TaskItem,
  type EventItem,
} from "../services/api";

interface Message {
  id: string;
  sender: "saturday" | "user";
  text: string;
  time: string;
}

const formatClock = (d: Date) =>
  d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });

/** Comandos rápidos del panel derecho (equivalente a los bullets de la imagen) */
const quickCommands = [
  "Extraer métricas",
  "Resumen bandeja",
  "Escaneo tendencias",
  "Plan de hoy",
  "Revisión semanal",
  "Reporte AM",
  "Tendencias GH",
  "YT semanal",
  "Plan mañana",
  "Limpieza bóveda",
];

/** Informes del panel izquierdo */
const reportShortcuts = ["Informe breve", "Informe mental", "Informe del mercado", "Plan diario"];

/** Quita el timestamp del nombre de archivo para mostrar un título legible */
const prettifyNoteName = (name: string) =>
  name
    .replace(/^\d{4}-\d{2}-\d{2}_\d{6}_/, "")
    .replace(/\.md$/, "")
    .replace(/-/g, " ");

interface HomeProps {
  onNavigateNews?: () => void;
  onNavigateSettings?: () => void;
}

export default function Home({ onNavigateNews, onNavigateSettings }: HomeProps) {
  const [now, setNow] = useState(new Date());
  const [inputValue, setInputValue] = useState("");
  const [sending, setSending] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [statusError, setStatusError] = useState(false);
  const [weather, setWeather] = useState<WeatherResponse | null>(null);
  const [system, setSystem] = useState<SystemStats | null>(null);
  const [vaultStats, setVaultStats] = useState<VaultStats | null>(null);
  const [recentOutputs, setRecentOutputs] = useState<VaultNote[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "saturday",
      text: "Hola, soy SATURDAY. Conectando con el backend...",
      time: formatClock(new Date()),
    },
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const clock = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(clock);
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

  const refreshSystem = useCallback(async () => {
    try {
      setSystem(await getSystemStats());
    } catch {
      setSystem(null);
    }
  }, []);

  const refreshVault = useCallback(async () => {
    try {
      const [stats, outputs] = await Promise.all([
        getVaultStats(),
        getVaultNotes("outputs"),
      ]);
      setVaultStats(stats);
      setRecentOutputs(outputs.slice(-4).reverse());
    } catch {
      setVaultStats(null);
      setRecentOutputs([]);
    }
  }, []);

  const refreshAgenda = useCallback(async () => {
    try {
      setTasks(await getTasksList());
    } catch {
      setTasks([]);
    }
    try {
      setEvents(await getEventsToday());
    } catch {
      setEvents([]);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    refreshWeather();
    refreshSystem();
    refreshVault();
    refreshAgenda();
    const statusInterval = setInterval(refreshStatus, 15000);
    const weatherInterval = setInterval(refreshWeather, 5 * 60 * 1000);
    const systemInterval = setInterval(refreshSystem, 10000);
    const vaultInterval = setInterval(refreshVault, 20000);
    const agendaInterval = setInterval(refreshAgenda, 60000);
    return () => {
      clearInterval(statusInterval);
      clearInterval(weatherInterval);
      clearInterval(systemInterval);
      clearInterval(vaultInterval);
      clearInterval(agendaInterval);
    };
  }, [refreshStatus, refreshWeather, refreshSystem, refreshVault, refreshAgenda]);

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

    const userMsg: Message = { id: Date.now().toString(), sender: "user", text: value, time: formatClock(new Date()) };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setSending(true);

    try {
      const result = await apiSendMessage(value);
      const replyText = result.response || "No obtuve respuesta del backend.";
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), sender: "saturday", text: replyText, time: formatClock(new Date()) },
      ]);

      speakText(replyText.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F000}-\u{1FAFF}\u{200D}\u{20E3}\u{E0020}-\u{E007F}]/gu, "").replace(/\s{2,}/g, " ").trim()).then(() => setSpeaking(false));
      setSpeaking(true);

      // Si el backend interpretó un comando de navegación (ej: "abrir noticias"),
      // cambiamos de vista en vez de solo mostrar la respuesta en el chat.
      if (result.navigate === "news" && onNavigateNews) {
        setTimeout(() => onNavigateNews(), 400);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "saturday",
          text: "No pude comunicarme con el backend. Verificá que esté corriendo.",
          time: formatClock(new Date()),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  // Reconocimiento de voz: al terminar de hablar, el texto final se manda solo
  // por el mismo pipeline que el chat de texto (sendMessage -> /api/chat).
  const speech = useSpeechRecognition({
    lang: "es-CL",
    onFinalResult: (transcript) => sendMessage(transcript),
  });

  const isOnline = !!status && status.status === "online";
  const activeModulesCount = status ? Object.values(status.modules).filter(Boolean).length : 0;
  const cpuPct = system ? Math.round(system.cpu_percent) : 0;
  const lastMessage = messages[messages.length - 1];

  return (
    <div className="vault">
      <div className="vault__bg-grid" />
      <div className="vault__scanline" />

      {/* ===== TOPBAR ===== */}
      <header className="vault-topbar">
        <div className="vault-topbar__brand">
          <span className="vault-logo">V.A.U.L.T.</span>
          <span className="vault-subtitle">INTELIGENCIA CENTRALIZADA</span>
        </div>
        <nav className="vault-topbar__nav">
          <span>NÚCLEO</span>
          <span>IDEAS</span>
          <span>ENLACE</span>
          <span className="dim">·</span>
          <span>EN LÍNEA</span>
          <span className="vault-topbar__link" onClick={onNavigateNews}>NOTICIAS</span>
          <span className="vault-topbar__link" onClick={onNavigateSettings}>SETTINGS</span>
          <span className="vault-topbar__active">ACTIVE</span>
        </nav>
        <div className="vault-topbar__clock">
          <span className="vault-topbar__clock-time">{formatClock(now)}</span>
          <span className="vault-topbar__clock-label">HORA DEL SISTEMA</span>
        </div>
      </header>

      <div className="vault-main">
        {/* ===== COLUMNA IZQUIERDA ===== */}
        <aside className="vault-col vault-col--left">
          <div className="vault-panel-title">VITALES DEL SISTEMA</div>

          <div className="vault-metric">
            <div className="vault-metric__label">
              <Users size={12} /> MÓDULOS ACTIVOS
            </div>
            <div className="vault-metric__value">
              {status ? `${activeModulesCount}/${Object.values(status.modules).length}` : "—"}
              <span className="vault-metric__delta">{isOnline ? "sistema en línea" : "sin conexión"}</span>
            </div>
          </div>

          <div className="vault-metric">
            <div className="vault-metric__label">
              <MessageSquare size={12} /> NOTAS EN LA BÓVEDA
            </div>
            <div className="vault-metric__value">
              {vaultStats ? vaultStats.wiki_count + vaultStats.raw_count + vaultStats.outputs_count : "—"}
              <span className="vault-metric__delta">
                {vaultStats ? `${vaultStats.graph_edges} enlaces` : "cargando..."}
              </span>
            </div>
          </div>

          <div className="vault-metric">
            <div className="vault-metric__label">
              <ListChecks size={12} /> TAREAS PENDIENTES
            </div>
            <div className="vault-metric__value">
              {tasks.length}
              <span className="vault-metric__delta">Notion</span>
            </div>
          </div>

          <div className="vault-metric">
            <div className="vault-metric__label">
              <Percent size={12} /> USO DE LA CPU
            </div>
            <div className="vault-metric__value">
              {system ? `${cpuPct}%` : "—"}
              <span className="vault-metric__delta">
                {system ? `RAM ${Math.round(system.ram_percent)}%` : "servidor"}
              </span>
            </div>
            <div className="vault-bar">
              <div className="vault-bar__fill" style={{ width: `${cpuPct}%` }} />
            </div>
          </div>

          <div className="vault-panel-title vault-panel-title--tight">DIRECTIVAS (+2.8)</div>
          <ul className="vault-list">
            <li>Construido para el modo de JARVIS</li>
            <li>Conectar la voz-habilidad con el canal active</li>
            <li>Bloquear pestañas — flujos — miniaturas</li>
            <li>Recuperar contexto</li>
          </ul>

          <div className="vault-panel-title vault-panel-title--tight">INFORMES</div>
          <ul className="vault-linklist">
            {recentOutputs.length > 0
              ? recentOutputs.map((note) => (
                  <li key={note.path} onClick={() => sendMessage(`leer nota ${note.path}`)}>
                    <span>{prettifyNoteName(note.name)}</span>
                    <ChevronRight size={12} />
                  </li>
                ))
              : reportShortcuts.map((r) => (
                  <li key={r} onClick={() => sendMessage(r)}>
                    <span>{r}</span>
                    <ChevronRight size={12} />
                  </li>
                ))}
          </ul>
        </aside>

        {/* ===== COLUMNA CENTRAL ===== */}
        <main className="vault-col vault-col--center">
          <div className="vault-sphere-wrap">
            <VaultGraph active={speech.listening || sending || speaking} size={460} />
            <div className="vault-sphere-count">
              <span className="vault-sphere-count__num">
                {vaultStats
                  ? (vaultStats.wiki_count + vaultStats.raw_count + vaultStats.outputs_count).toLocaleString("es-ES")
                  : "—"}
              </span>
              <span className="vault-sphere-count__label">NOTAS</span>
            </div>
          </div>

          <div className="vault-sphere-caption">MEMORIA DE LA BÓVEDA — NOTAS ENLAZADAS</div>

          <div className="vault-status-row">
            <span className={`vault-status-dot ${isOnline ? "vault-status-dot--on" : "vault-status-dot--off"}`} />
            {isOnline ? "SISTEMA EN LÍNEA" : statusError ? "SIN CONEXIÓN AL BACKEND" : "CONECTANDO..."}
            {weather && (
              <>
                <span className="vault-status-sep">|</span>
                <MapPin size={11} /> {weather.city} {weather.temp}°C
              </>
            )}
          </div>

          <div className="vault-composer">
            <span className="vault-composer__prompt">SATURDAY /</span>
            <input
              type="text"
              placeholder={
                speech.listening
                  ? speech.interimTranscript || "Escuchando..."
                  : "Escribe una instrucción o comando..."
              }
              value={speech.listening ? speech.interimTranscript : inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={sending || speech.listening}
            />
            <button
              className={`vault-composer__mic ${speech.listening ? "vault-composer__mic--active" : ""}`}
              onClick={speech.toggle}
              disabled={!speech.supported}
              title={
                !speech.supported
                  ? "Tu navegador no soporta reconocimiento de voz (probá con Chrome o Edge)"
                  : speech.listening
                    ? "Detener y escuchar"
                    : "Activar voz"
              }
            >
              {speech.listening ? <Mic size={14} /> : <MicOff size={14} />}
            </button>
            <button className="vault-composer__send" onClick={() => sendMessage()} disabled={sending || !inputValue.trim()}>
              <Send size={14} />
            </button>
          </div>

          {speech.error && (
            <div className="vault-speech-error">
              🎙️ No pude usar el micrófono ({speech.error === "not-allowed" ? "permiso denegado" : speech.error}).
            </div>
          )}

          <div className="vault-last-msg">
            <span className="vault-last-msg__tag">saturday</span>
            {sending ? "pensando..." : speech.listening ? "escuchando..." : lastMessage?.text}
          </div>
          <div ref={chatEndRef} />
        </main>

        {/* ===== COLUMNA DERECHA ===== */}
        <aside className="vault-col vault-col--right">
          <div className="vault-panel-title">PANEL DE COMANDOS</div>
          <ul className="vault-linklist vault-linklist--grid">
            {quickCommands.map((c) => (
              <li key={c} onClick={() => sendMessage(c)}>
                <span>{c}</span>
              </li>
            ))}
          </ul>
          <div className="vault-instruction-line">
            INTENCIONES ESCRIBEN AL SISTEMA/COLA ›<br />
            EJECUTA EL COMBINADOR
          </div>

          <div className="vault-panel-title vault-panel-title--tight">AGENDA / HOY</div>
          <ul className="vault-agenda">
            {events.length > 0 ? (
              events.map((e, i) => (
                <li key={`${e.title}-${i}`}>
                  <span className="vault-agenda__time">{e.time}</span> {e.title}
                </li>
              ))
            ) : (
              <li className="vault-agenda__empty">Sin eventos programados para hoy.</li>
            )}
          </ul>

          <div className="vault-panel-title vault-panel-title--tight">AUDIO E/S</div>
          <div className="vault-audio-row">
            TTS / LOCAL
            <span className="vault-audio-state">{speech.listening ? "ESCUCHANDO..." : "EJECUTÁNDOSE..."}</span>
          </div>

          <div className="vault-panel-title vault-panel-title--tight">
            <Lock size={11} /> YA DENTRO
          </div>
          <p className="vault-security-note">
            Todo lo que Saturday guarda o envía queda registrado como archivo en la bóveda local.
          </p>
          <p className="vault-security-note vault-security-note--dim">
            <Cpu size={11} /> {system ? `CPU ${cpuPct}% · RAM ${Math.round(system.ram_percent)}%` : "Servidor Flask local"}. Sin base de datos externa.
          </p>
        </aside>
      </div>
    </div>
  );
}