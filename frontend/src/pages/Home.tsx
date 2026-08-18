import React, { useState, useEffect, useRef } from "react";
import {
  Settings,
  RefreshCw,
  Cloud,
  Camera as CameraIcon,
  Power,
  Clock,
  Maximize2,
  Trash2,
  Download,
  Send,
  Mic,
  Keyboard,
  MapPin,
} from "lucide-react";
import "./JarvisInterface.css";

interface Message {
  id: string;
  sender: "jarvis" | "user";
  text: string;
  time: string;
}

const formatTime = (d: Date) =>
  d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit", hour12: true });

const formatDate = (d: Date) =>
  d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

const formatUptime = (seconds: number) => {
  const h = Math.floor(seconds / 3600).toString().padStart(2, "0");
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${h}:${m}:${s}`;
};

export default function JarvisInterface() {
  const [now, setNow] = useState(new Date());
  const [uptime, setUptime] = useState(7 * 60 + 19); // seconds
  const [cameraOn, setCameraOn] = useState(false);
  const [listening, setListening] = useState(true);
  const [inputValue, setInputValue] = useState("");
  const [commandCount, setCommandCount] = useState(0);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "jarvis",
      text: "Hello, I am JARVIS. JARVIS backend is offline. Some features may be limited. How can I assist you today sir?",
      time: "2:45 PM",
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

  const systemStats = {
    cpu: 8,
    ram: 44,
    ramGb: "7 GB",
    disk: "439/475 GB",
  };

  const weather = {
    temp: "25.2°C",
    location: "Quezon City, PH",
    condition: "overcast clouds",
    humidity: "94%",
    wind: "5.8 m/s",
    feelsLike: "26.3°C",
  };

  const systemLoad = 26;

  const sendMessage = () => {
    if (!inputValue.trim()) return;
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputValue.trim(),
      time: formatTime(new Date()),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setCommandCount((c) => c + 1);

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "jarvis",
          text: "Backend connection unavailable — running in limited offline mode, sir.",
          time: formatTime(new Date()),
        },
      ]);
    }, 700);
  };

  const clearConversation = () => setMessages([]);

  const extractConversation = () => {
    const text = messages.map((m) => `[${m.time}] ${m.sender === "jarvis" ? "JARVIS" : "You"}: ${m.text}`).join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "jarvis-conversation.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="jarvis">
      <div className="jarvis__bg-grid" />

      {/* ===== TOP BAR ===== */}
      <header className="jarvis-topbar">
        <div className="jarvis-topbar__brand">
          <span className="jarvis-logo">J.A.R.V.I.S</span>
          <span className="pill pill--online">
            <span className="dot dot--green" />
            Online
          </span>
        </div>

        <div className="jarvis-topbar__center pill">
          <Clock size={14} />
          <span>{formatTime(now)}</span>
          <span className="topbar-sep">|</span>
          <span>{formatDate(now)}</span>
        </div>

        <div className="jarvis-topbar__right">
          <span className="pill">
            <MapPin size={13} />
            {weather.temp} <span className="muted">Quezon City</span>
          </span>
          <button className="icon-square-btn">
            <Settings size={16} />
          </button>
        </div>
      </header>

      {/* ===== MAIN GRID ===== */}
      <div className="jarvis-main">
        {/* ===== LEFT SIDEBAR ===== */}
        <aside className="jarvis-sidebar">
          <section className="panel">
            <div className="panel__head">
              <div className="panel__title">
                <Settings size={15} className="accent" />
                System Stats
              </div>
              <button className="ghost-icon-btn">
                <RefreshCw size={13} />
              </button>
            </div>

            <div className="stat-row">
              <div className="stat-row__label">
                <span>CPU Usage</span>
                <span>{systemStats.cpu}%</span>
              </div>
              <div className="bar">
                <div className="bar__fill bar__fill--cyan" style={{ width: `${systemStats.cpu}%` }} />
              </div>
            </div>

            <div className="stat-row">
              <div className="stat-row__label">
                <span>RAM Usage</span>
                <span>{systemStats.ramGb}</span>
              </div>
              <div className="bar">
                <div className="bar__fill bar__fill--cyan" style={{ width: `${systemStats.ram}%` }} />
              </div>
            </div>

            <div className="mini-stats">
              <div className="mini-stat">
                <div className="mini-stat__label">CPU</div>
                <div className="mini-stat__value">{systemStats.cpu}%</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Memory</div>
                <div className="mini-stat__value">{systemStats.ram}%</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Disk</div>
                <div className="mini-stat__value">{systemStats.disk}</div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel__head">
              <div className="panel__title">
                <Cloud size={15} className="accent" />
                Weather
              </div>
              <button className="ghost-icon-btn">
                <RefreshCw size={13} />
              </button>
            </div>

            <div className="weather-main">
              <div>
                <div className="weather-temp">{weather.temp}</div>
                <div className="weather-loc">{weather.location}</div>
                <div className="weather-cond">{weather.condition}</div>
              </div>
              <Cloud size={36} className="weather-icon" />
            </div>

            <div className="mini-stats mini-stats--3">
              <div className="mini-stat">
                <div className="mini-stat__label">Humidity</div>
                <div className="mini-stat__value">{weather.humidity}</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Wind</div>
                <div className="mini-stat__value">{weather.wind}</div>
              </div>
              <div className="mini-stat">
                <div className="mini-stat__label">Feels Like</div>
                <div className="mini-stat__value">{weather.feelsLike}</div>
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
                <span className="load-row__tag">Moderate</span>
                <span>{systemLoad}%</span>
              </div>
              <div className="bar">
                <div className="bar__fill bar__fill--amber" style={{ width: `${systemLoad}%` }} />
              </div>
            </div>
          </section>
        </aside>

        {/* ===== CENTER ORB ===== */}
        <main className="jarvis-center">
          <div className="orb-wrap">
            <div className="orb-ring orb-ring--outer" />
            <div className="orb-ring orb-ring--mid" />
            <div className="orb-core">
              <div className="orb-core__dots">
                <span />
                <span />
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>

          <h1 className="orb-title">J.A.R.V.I.S</h1>

          <button className="listening-pill" onClick={() => setListening((v) => !v)}>
            <span className={`dot ${listening ? "dot--green" : "dot--gray"}`} />
            {listening ? "Listening for wake word..." : "Wake word paused"}
          </button>

          <div className="center-controls">
            <button className="round-btn">
              <CameraIcon size={18} />
            </button>
            <button className={`round-btn round-btn--mic ${listening ? "round-btn--mic-active" : ""}`}>
              <Mic size={20} />
            </button>
            <button className="round-btn">
              <Keyboard size={18} />
            </button>
          </div>

          <div className="carousel-dots">
            <span className="carousel-dot carousel-dot--active" />
            <span className="carousel-dot" />
            <span className="carousel-dot" />
            <span className="carousel-dot" />
          </div>
        </main>

        {/* ===== RIGHT: CONVERSATION ===== */}
        <aside className="jarvis-conversation">
          <div className="conversation__head">
            <span className="conversation__title">Conversation</span>
            <div className="conversation__actions">
              <button className="text-btn" onClick={clearConversation}>
                <Trash2 size={13} />
                Clear
              </button>
              <button className="text-btn text-btn--accent" onClick={extractConversation}>
                <Download size={13} />
                Extract Conversation
              </button>
            </div>
          </div>

          <div className="conversation__body">
            {messages.map((m) => (
              <div key={m.id} className={`msg-row msg-row--${m.sender}`}>
                <div className={`msg-bubble msg-bubble--${m.sender}`}>
                  <p>{m.text}</p>
                  <span className="msg-time">{m.time}</span>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="conversation__input">
            <input
              type="text"
              placeholder="Type a message..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage} disabled={!inputValue.trim()}>
              <Send size={16} />
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}