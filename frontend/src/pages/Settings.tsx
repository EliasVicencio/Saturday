import { useState, useEffect, useCallback } from "react";
import { Shield, Camera, Mic, MapPin, Activity, Eye, Zap, ChevronRight, RotateCcw } from "lucide-react";
import {
  getPrivacy, setPrivacy, getVisionStatus, captureVision, getEvents,
  type PrivacyState, type VisionStatus, type VisionCapture, type EventItem2,
} from "../services/api";

export default function Settings() {
  const [privacy, setPrivacyState] = useState<PrivacyState | null>(null);
  const [vision, setVision] = useState<VisionStatus | null>(null);
  const [capture, setCapture] = useState<VisionCapture | null>(null);
  const [capturing, setCapturing] = useState(false);
  const [events, setEvents] = useState<EventItem2[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [p, v, e] = await Promise.all([getPrivacy(), getVisionStatus(), getEvents(10)]);
      setPrivacyState(p);
      setVision(v);
      setEvents(e);
    } catch (e) {
      console.error("Error loading settings:", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const togglePrivacy = async (feature: string) => {
    if (!privacy) return;
    const current = (privacy as Record<string, boolean>)[feature];
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

  const doCapture = async () => {
    setCapturing(true);
    setCapture(null);
    try {
      const res = await captureVision("Describe brevemente lo que ves");
      setCapture(res);
      const evts = await getEvents(10);
      setEvents(evts);
    } catch (e) {
      setCapture({ captured: false, simulated: false, description: "Error al capturar", timestamp: null });
    }
    setCapturing(false);
  };

  if (loading) {
    return (
      <div style={{ color: "#94a3b8", padding: "2rem", fontFamily: "monospace" }}>
        Cargando nivel 4...
      </div>
    );
  }

  const privacyItems = privacy ? [
    { key: "camera_enabled", label: "Camara", icon: <Camera size={14} /> },
    { key: "microphone_enabled", label: "Microfono", icon: <Mic size={14} /> },
    { key: "location_enabled", label: "Ubicacion", icon: <MapPin size={14} /> },
    { key: "ambient_sensors", label: "Sensores", icon: <Activity size={14} /> },
    { key: "auto_save_images", label: "Auto-guardar imagenes", icon: <Eye size={14} /> },
  ] : [];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Shield size={18} />
        <span>NIVEL 4 — CONTROL</span>
      </div>

      {/* PRIVACY */}
      <section style={styles.section}>
        <div style={styles.sectionTitle}>
          <Shield size={13} /> PRIVACIDAD
        </div>
        <div style={styles.privacyGrid}>
          {privacyItems.map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => togglePrivacy(key)}
              style={{
                ...styles.privacyBtn,
                ...(privacy[key as keyof PrivacyState] ? styles.privacyBtnOn : styles.privacyBtnOff),
              }}
            >
              {icon}
              <span>{label}</span>
              <span style={{ marginLeft: "auto", fontSize: 10 }}>
                {privacy[key as keyof PrivacyState] ? "ON" : "OFF"}
              </span>
            </button>
          ))}
        </div>
        <div style={styles.killRow}>
          <button onClick={killAll} style={styles.killBtn}>
            <Zap size={12} /> KILL ALL
          </button>
          <button onClick={restoreAll} style={styles.restoreBtn}>
            <RotateCcw size={12} /> RESTORE ALL
          </button>
        </div>
      </section>

      {/* VISION */}
      <section style={styles.section}>
        <div style={styles.sectionTitle}>
          <Eye size={13} /> VISION
        </div>
        <div style={styles.visionRow}>
          <span style={styles.badge}>
            Camara: {vision?.camera.available ? "OK" : "No disponible"}
          </span>
          <span style={styles.badge}>
            LLM Vision: {vision?.vision_model ? "Activo" : "Inactivo"}
          </span>
        </div>
        <button onClick={doCapture} disabled={capturing} style={styles.captureBtn}>
          {capturing ? "Capturando..." : "Capturar y describir"}
        </button>
        {capture && (
          <div style={styles.captureResult}>
            <div style={styles.captureMeta}>
              {capture.simulated ? "Simulado" : "Real"} {capture.timestamp ? `- ${new Date(capture.timestamp).toLocaleTimeString()}` : ""}
            </div>
            {capture.description && (
              <div style={styles.captureDesc}>{capture.description}</div>
            )}
          </div>
        )}
      </section>

      {/* EVENTS */}
      <section style={styles.section}>
        <div style={styles.sectionTitle}>
          <Zap size={13} /> EVENTOS RECIENTES
        </div>
        <div style={styles.eventsList}>
          {events.length === 0 && <div style={styles.empty}>Sin eventos</div>}
          {events.map((ev, i) => (
            <div key={i} style={styles.eventItem}>
              <span style={styles.eventName}>{ev.name}</span>
              <span style={styles.eventSource}>{ev.source}</span>
              {Object.keys(ev.data).length > 0 && (
                <span style={styles.eventData}>{JSON.stringify(ev.data).slice(0, 40)}</span>
              )}
            </div>
          ))}
        </div>
      </section>

      <button onClick={refresh} style={styles.refreshBtn}>
        <RotateCcw size={12} /> Actualizar
      </button>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    fontFamily: "monospace",
    color: "#e2e8f0",
    padding: "1.5rem",
    maxWidth: 600,
    margin: "0 auto",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: 2,
    marginBottom: 20,
    color: "#60a5fa",
  },
  section: {
    marginBottom: 20,
    padding: 16,
    background: "rgba(15,23,42,0.6)",
    border: "1px solid rgba(96,165,250,0.15)",
    borderRadius: 8,
  },
  sectionTitle: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 1.5,
    color: "#94a3b8",
    marginBottom: 12,
  },
  privacyGrid: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  privacyBtn: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 12px",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 12,
    fontFamily: "monospace",
    color: "#e2e8f0",
    transition: "all 0.15s",
  },
  privacyBtnOn: {
    background: "rgba(34,197,94,0.15)",
    border: "1px solid rgba(34,197,94,0.3)",
  },
  privacyBtnOff: {
    background: "rgba(239,68,68,0.15)",
    border: "1px solid rgba(239,68,68,0.3)",
  },
  killRow: {
    display: "flex",
    gap: 8,
    marginTop: 12,
  },
  killBtn: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    padding: "8px 0",
    border: "1px solid rgba(239,68,68,0.4)",
    borderRadius: 6,
    background: "rgba(239,68,68,0.15)",
    color: "#fca5a5",
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 600,
    fontFamily: "monospace",
  },
  restoreBtn: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    padding: "8px 0",
    border: "1px solid rgba(34,197,94,0.4)",
    borderRadius: 6,
    background: "rgba(34,197,94,0.15)",
    color: "#86efac",
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 600,
    fontFamily: "monospace",
  },
  visionRow: {
    display: "flex",
    gap: 8,
    marginBottom: 12,
  },
  badge: {
    fontSize: 10,
    padding: "4px 8px",
    borderRadius: 4,
    background: "rgba(96,165,250,0.1)",
    border: "1px solid rgba(96,165,250,0.2)",
    color: "#93c5fd",
  },
  captureBtn: {
    width: "100%",
    padding: "10px 0",
    border: "1px solid rgba(96,165,250,0.3)",
    borderRadius: 6,
    background: "rgba(96,165,250,0.1)",
    color: "#93c5fd",
    cursor: "pointer",
    fontSize: 12,
    fontFamily: "monospace",
  },
  captureResult: {
    marginTop: 12,
    padding: 12,
    borderRadius: 6,
    background: "rgba(15,23,42,0.5)",
    border: "1px solid rgba(96,165,250,0.1)",
  },
  captureMeta: {
    fontSize: 10,
    color: "#64748b",
    marginBottom: 6,
  },
  captureDesc: {
    fontSize: 12,
    color: "#e2e8f0",
    lineHeight: 1.5,
  },
  eventsList: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  eventItem: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 8px",
    borderRadius: 4,
    background: "rgba(15,23,42,0.4)",
    fontSize: 11,
  },
  eventName: {
    color: "#60a5fa",
    fontWeight: 600,
  },
  eventSource: {
    color: "#64748b",
    fontSize: 10,
  },
  eventData: {
    color: "#94a3b8",
    fontSize: 10,
    marginLeft: "auto",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  empty: {
    color: "#475569",
    fontSize: 12,
    textAlign: "center" as const,
    padding: 12,
  },
  refreshBtn: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    width: "100%",
    padding: "10px 0",
    border: "1px solid rgba(96,165,250,0.2)",
    borderRadius: 6,
    background: "transparent",
    color: "#64748b",
    cursor: "pointer",
    fontSize: 11,
    fontFamily: "monospace",
  },
};
