import { useState, useEffect, useCallback, useRef } from "react";
import { Shield, Camera, Mic, MapPin, Activity, Eye, Zap, RotateCcw, ChevronLeft } from "lucide-react";
import {
  getPrivacy, setPrivacy, getVisionStatus, captureVision, captureFromDevice as captureFromDeviceApi, getEvents,
  type PrivacyState, type VisionStatus, type VisionCapture, type EventItem2,
} from "../services/api";

interface Props {
  onBack?: () => void;
}

export default function Settings({ onBack }: Props) {
  const [privacy, setPrivacyState] = useState<PrivacyState | null>(null);
  const [vision, setVision] = useState<VisionStatus | null>(null);
  const [capture, setCapture] = useState<VisionCapture | null>(null);
  const [capturing, setCapturing] = useState(false);
  const [events, setEvents] = useState<EventItem2[]>([]);
  const [loading, setLoading] = useState(true);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [p, v, e] = await Promise.all([getPrivacy(), getVisionStatus(), getEvents(10)]);
      setPrivacyState(p);
      setVision(v);
      setEvents(e);
    } catch {
      console.error("Error loading settings");
    }
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [cameraStream]);

  const togglePrivacy = async (feature: string) => {
    if (!privacy) return;
    const current = privacy[feature as keyof PrivacyState] as boolean;
    const res = await setPrivacy(feature, !current);
    setPrivacyState(res.state);
  };

  const killAll = async () => {
    const res = await setPrivacy("kill_all");
    setPrivacyState(res.state);
  };

  const restoreAll = async () => {
    const res = await setPrivacy("restore_all");
    setPrivacyState(res.state);
  };

  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
      });
      setCameraStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch {
      setCameraError("No se pudo acceder a la camara. Permiso denegado o sin dispositivo.");
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
      setCameraStream(null);
    }
  };

  const captureFromDevice = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setCapturing(true);
    setCapture(null);
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0);
    }
    const base64 = canvas.toDataURL("image/jpeg", 0.85).split(",")[1];
    try {
      const response = await captureFromDeviceApi(base64, "Describe brevemente lo que ves");
      setCapture(response);
      const evts = await getEvents(10);
      setEvents(evts);
    } catch {
      setCapture({ captured: false, simulated: false, description: "Error al enviar imagen", timestamp: null });
    }
    setCapturing(false);
  };

  const doServerCapture = async () => {
    setCapturing(true);
    setCapture(null);
    try {
      const res = await captureVision("Describe brevemente lo que ves");
      setCapture(res);
      const evts = await getEvents(10);
      setEvents(evts);
    } catch {
      setCapture({ captured: false, simulated: false, description: "Error al capturar", timestamp: null });
    }
    setCapturing(false);
  };

  if (loading) {
    return (
      <div style={{ ...C.container, display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <span style={{ color: "var(--gold-dim)" }}>Cargando nivel 4...</span>
      </div>
    );
  }

  const privacyItems = privacy ? [
    { key: "camera_enabled", label: "Camara", icon: <Camera size={13} /> },
    { key: "microphone_enabled", label: "Microfono", icon: <Mic size={13} /> },
    { key: "location_enabled", label: "Ubicacion", icon: <MapPin size={13} /> },
    { key: "ambient_sensors", label: "Sensores ambientales", icon: <Activity size={13} /> },
    { key: "auto_save_images", label: "Auto-guardar imagenes", icon: <Eye size={13} /> },
  ] : [];

  return (
    <div className="vault" style={{ position: "relative" }}>
      <div className="vault__bg-grid" />
      <div className="vault__scanline" />

      {/* HEADER */}
      <header style={C.header}>
        <button onClick={onBack} style={C.backBtn}>
          <ChevronLeft size={16} /> VOLVER
        </button>
        <div style={C.headerTitle}>
          <Shield size={16} />
          <span>CONTROL NIVEL 4</span>
        </div>
        <div style={{ width: 80 }} />
      </header>

      <div style={C.body}>
        {/* PRIVACIDAD */}
        <section style={C.section}>
          <div style={C.sectionLabel}>
            <Shield size={11} /> PRIVACIDAD
          </div>
          <div style={C.grid}>
            {privacyItems.map(({ key, label, icon }) => {
              const on = privacy[key as keyof PrivacyState] as boolean;
              return (
                <button
                  key={key}
                  onClick={() => togglePrivacy(key)}
                  style={{ ...C.toggle, ...(on ? C.toggleOn : C.toggleOff) }}
                >
                  {icon}
                  <span>{label}</span>
                  <span style={{ marginLeft: "auto", fontSize: 9, opacity: 0.7 }}>
                    {on ? "ON" : "OFF"}
                  </span>
                </button>
              );
            })}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button onClick={killAll} style={C.killBtn}>
              <Zap size={11} /> KILL ALL
            </button>
            <button onClick={restoreAll} style={C.restoreBtn}>
              <RotateCcw size={11} /> RESTORE
            </button>
          </div>
        </section>

        {/* VISION */}
        <section style={C.section}>
          <div style={C.sectionLabel}>
            <Eye size={11} /> VISION
          </div>

          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            <span style={C.badge}>
              Servidor: {vision?.camera.available ? "OK" : "sin camara"}
            </span>
            <span style={C.badge}>
              LLM: {vision?.vision_model ? "Activo" : "Inactivo"}
            </span>
          </div>

          {/* Camara del navegador */}
          <div style={{ marginBottom: 12 }}>
            {!cameraStream ? (
              <button onClick={startCamera} style={C.captureBtn}>
                <Camera size={13} /> Abrir camara del dispositivo
              </button>
            ) : (
              <div>
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  style={{ width: "100%", borderRadius: 6, background: "#000", maxHeight: 300, objectFit: "cover" }}
                />
                <canvas ref={canvasRef} style={{ display: "none" }} />
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <button onClick={captureFromDevice} disabled={capturing} style={{ ...C.captureBtn, flex: 1 }}>
                    {capturing ? "Enviando..." : "Capturar y describir"}
                  </button>
                  <button onClick={stopCamera} style={{ ...C.captureBtn, background: "rgba(226,102,90,0.15)", borderColor: "rgba(226,102,90,0.3)", color: "#e2665a", flex: "none", padding: "0 16px" }}>
                    Cerrar
                  </button>
                </div>
              </div>
            )}
            {cameraError && <div style={{ fontSize: 11, color: "#e2665a", marginTop: 8 }}>{cameraError}</div>}
          </div>

          {/* Captura desde servidor */}
          <button onClick={doServerCapture} disabled={capturing} style={C.serverBtn}>
            Capturar desde servidor (sin camara local)
          </button>

          {capture && (
            <div style={C.captureResult}>
              <div style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 4 }}>
                {capture.simulated ? "SIMULADO" : "REAL"} {capture.timestamp ? `- ${new Date(capture.timestamp).toLocaleTimeString()}` : ""}
              </div>
              {capture.description && (
                <div style={{ fontSize: 12, lineHeight: 1.5 }}>{capture.description}</div>
              )}
            </div>
          )}
        </section>

        {/* EVENTOS */}
        <section style={C.section}>
          <div style={C.sectionLabel}>
            <Zap size={11} /> EVENTOS RECIENTES
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {events.length === 0 && <div style={{ color: "var(--text-faint)", fontSize: 11, textAlign: "center", padding: 12 }}>Sin eventos</div>}
            {events.map((ev, i) => (
              <div key={i} style={C.eventRow}>
                <span style={{ color: "var(--gold)", fontWeight: 600, fontSize: 11 }}>{ev.name}</span>
                <span style={{ color: "var(--text-faint)", fontSize: 10, marginLeft: "auto" }}>
                  {Object.keys(ev.data).length > 0 ? JSON.stringify(ev.data).slice(0, 30) : ev.source}
                </span>
              </div>
            ))}
          </div>
        </section>

        <button onClick={refresh} style={C.refreshBtn}>
          <RotateCcw size={11} /> Actualizar
        </button>
      </div>
    </div>
  );
}

const C: Record<string, React.CSSProperties> = {
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 20px",
    borderBottom: "1px solid var(--panel-border)",
    background: "rgba(5,4,3,0.8)",
    backdropFilter: "blur(8px)",
    zIndex: 10,
  },
  backBtn: {
    display: "flex",
    alignItems: "center",
    gap: 4,
    background: "none",
    border: "1px solid var(--panel-border)",
    borderRadius: 4,
    color: "var(--gold-dim)",
    cursor: "pointer",
    fontSize: 11,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 1,
    padding: "6px 10px",
  },
  headerTitle: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    color: "var(--gold)",
    fontSize: 13,
    fontWeight: 700,
    letterSpacing: 2,
  },
  body: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 20px",
    maxWidth: 600,
    margin: "0 auto",
    width: "100%",
  },
  section: {
    marginBottom: 16,
    padding: 14,
    background: "rgba(214,178,94,0.03)",
    border: "1px solid var(--panel-border)",
    borderRadius: 6,
  },
  sectionLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: 1.5,
    color: "var(--gold-dim)",
    marginBottom: 12,
    textTransform: "uppercase" as const,
  },
  grid: {
    display: "flex",
    flexDirection: "column",
    gap: 5,
  },
  toggle: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "7px 10px",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    fontSize: 11,
    fontFamily: "'JetBrains Mono', monospace",
    color: "var(--text)",
    transition: "all 0.12s",
  },
  toggleOn: {
    background: "rgba(111,220,140,0.1)",
    border: "1px solid rgba(111,220,140,0.2)",
  },
  toggleOff: {
    background: "rgba(226,102,90,0.1)",
    border: "1px solid rgba(226,102,90,0.2)",
  },
  killBtn: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    padding: "7px 0",
    border: "1px solid rgba(226,102,90,0.3)",
    borderRadius: 4,
    background: "rgba(226,102,90,0.1)",
    color: "#e2665a",
    cursor: "pointer",
    fontSize: 10,
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 1,
  },
  restoreBtn: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    padding: "7px 0",
    border: "1px solid rgba(111,220,140,0.3)",
    borderRadius: 4,
    background: "rgba(111,220,140,0.1)",
    color: "#6fdc8c",
    cursor: "pointer",
    fontSize: 10,
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 1,
  },
  badge: {
    fontSize: 9,
    padding: "3px 7px",
    borderRadius: 3,
    background: "rgba(214,178,94,0.08)",
    border: "1px solid rgba(214,178,94,0.15)",
    color: "var(--gold-dim)",
    letterSpacing: 0.5,
  },
  captureBtn: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    padding: "10px 0",
    border: "1px solid var(--panel-border)",
    borderRadius: 4,
    background: "rgba(214,178,94,0.08)",
    color: "var(--gold)",
    cursor: "pointer",
    fontSize: 11,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 0.5,
  },
  serverBtn: {
    width: "100%",
    padding: "8px 0",
    border: "1px solid rgba(214,178,94,0.1)",
    borderRadius: 4,
    background: "transparent",
    color: "var(--text-faint)",
    cursor: "pointer",
    fontSize: 10,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  captureResult: {
    marginTop: 12,
    padding: 12,
    borderRadius: 4,
    background: "rgba(214,178,94,0.04)",
    border: "1px solid var(--panel-border)",
    color: "var(--text)",
  },
  eventRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "5px 8px",
    borderRadius: 3,
    background: "rgba(214,178,94,0.03)",
  },
  refreshBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    width: "100%",
    padding: "8px 0",
    border: "1px solid var(--panel-border)",
    borderRadius: 4,
    background: "transparent",
    color: "var(--text-faint)",
    cursor: "pointer",
    fontSize: 10,
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: 1,
  },
};
