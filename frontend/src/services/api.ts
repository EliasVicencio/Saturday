import axios from 'axios';

const isDev = import.meta.env.DEV;
const devError = (...args: unknown[]) => { if (isDev) console.error(...args); };
const devWarn = (...args: unknown[]) => { if (isDev) console.warn(...args); };

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const API_BASE_URL = API_URL;

let sessionToken: string | null = null;

async function fetchSessionToken(): Promise<string | null> {
  try {
    const res = await axios.post(API_URL + '/auth/session', {}, { timeout: 10000 });
    if (res.data && res.data.token) {
      sessionToken = res.data.token;
      return sessionToken;
    }
  } catch (e) {
    devError('Failed to fetch session token:', e);
  }
  return null;
}

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(async (config) => {
  if (!sessionToken) {
    await fetchSessionToken();
  }
  if (sessionToken) {
    config.headers['X-API-Key'] = sessionToken;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response && error.response.status === 401 && sessionToken) {
      sessionToken = null;
      const newToken = await fetchSessionToken();
      if (newToken) {
        error.config.headers['X-API-Key'] = newToken;
        return api.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);

fetchSessionToken();

// ===== INTERFACES BASICAS =====

export interface WeatherResponse {
  temp: number;
  feels_like: number;
  condition: string;
  humidity: number;
  wind: number;
  city: string;
  country: string;
}

export interface GreetingResponse {
  ready: boolean;
  text: string | null;
}

// NUEVA INTERFACIÃ“N CON 'id' PARA SOLUCIONAR ERROR TYPEScRIPT
export interface NewsItem {
  id: string;
  title: string;
  description: string;
  source: string;
}

// Panel de noticias
export interface NewsPanelData {
  headlines: NewsItem[];
  lastUpdate: string;
}

// ===== FUNCION AUXILIAR POLIFUNCIONAL =====
// Intenta extraer tÃ­tulo de: **1. TÃ­tulo**, **TÃ­tulo**, 1. TÃ­tulo
function extractTitleFromLine(line: string): string | null {
  // PatrÃ³n 1: **1. TÃ­tulo** (nÃºmero + punto + texto)
  const p1 = /^\*\*(\d+)\.\s(.+?)\*\*$/;
  const m1 = line.match(p1);
  if (m1) return m1[2];
  
  // PatrÃ³n 2: **TÃ­tulo** (solo negrita, sin nÃºmero)
  const p2 = /^\*\*(.+?)\*\*$/;
  const m2 = line.match(p2);
  if (m2) return m2[1];
  
  // PatrÃ³n 3: 1. TÃ­tulo (sin negrita, solo nÃºmero + punto + texto)
  const p3 = /^(\d+)\.\s(.+)$/;
  const m3 = line.match(p3);
  if (m3) return m3[2];
  
  return null;
}

// ===== FUNCIÃ“N PRINCIPAL GETNEWSPANEL =====
export const getNewsPanel = async (): Promise<NewsPanelData> => {
  try {
    const response = await api.get<{ response?: string; success?: boolean }>('/news');
    if (response.data.response) {
      const articles: NewsItem[] = [];
      const lines = response.data.response.split('\n');
      let currentTitle = '';
      let currentSource = '';
      
      for (const line of lines) {
        // 1. Intentar extraer tÃ­tulo con cualquiera de los 3 patrones
        const title = extractTitleFromLine(line);
        
        if (title) {
          // Guardar tÃ­tulo anterior antes de empezar el nuevo
          if (currentTitle) {
            articles.push({ id: `${articles.length + 1}`, title: currentTitle, description: '', source: currentSource });
          }
          currentTitle = title;
          currentSource = '';
        }
        // Detectar fuente: debe contener "ðŸ“Œ *Fuente:*"
        else if (line.includes('ðŸ“Œ *Fuente:*')) {
          const sm = line.match(/ðŸ“Œ \*Fuente:\*\s(.+)/);
          if (sm) currentSource = sm[1];
        }
        // Detectar descripciÃ³n: "ðŸ“ Texto" (opcional, se ignora por simplicidad)
        else if (line.startsWith('ðŸ“ ')) {
          // Se asocia descriptivamente al tÃ­tulo actual (ignoramos por simplicidad)
        }
      }
      // Empujar el Ãºltimo tÃ­tulo si quedÃ³ pendiente
      if (currentTitle) {
        articles.push({ id: `${articles.length + 1}`, title: currentTitle, description: '', source: currentSource });
      }
      
      return { headlines: articles, lastUpdate: new Date().toLocaleString() };
    }
    return { headlines: [], lastUpdate: 'Nunca' };
  } catch (error) {
    devError('Error obteniendo panel de noticias:', error);
    return { headlines: [], lastUpdate: 'Error' };
  }
};

// ===== FUNCIÃ“N GETWEATHER (OBLIGATORIA PARA Home.tsx) =====
export const getWeather = async (): Promise<WeatherResponse> => {
  const response = await api.get<WeatherResponse>('/weather');
  return response.data;
};

// ===== ENVÃO DE MENSAJES =====

export const sendMessage = async (message: string): Promise<ChatResponse> => {
  const response = await api.post('/chat', { message });
  return response.data;
};

export const getStatus = async (): Promise<StatusResponse> => {
  const response = await api.get('/status');
  return response.data;
};

export const getGreeting = async (): Promise<GreetingResponse> => {
  const response = await api.get<GreetingResponse>('/greeting');
  return response.data;
};

export const speakText = async (text: string): Promise<boolean> => {
  if (!text) return false;

  try {
    const response = await api.post<SpeakResponse>('/speak', { text });
    const data = response.data;

    if (data.audio) {
      const audioBytes = Uint8Array.from(atob(data.audio), (c) => c.charCodeAt(0));
      const audioBlob = new Blob([audioBytes], { type: 'audio/mp3' });
      const audioUrl = URL.createObjectURL(audioBlob);

      const audio = new Audio(audioUrl);

      return new Promise((resolve) => {
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          resolve(true);
        };

        audio.onerror = (e) => {
          devWarn('Error reproduciendo audio:', e);
          URL.revokeObjectURL(audioUrl);
          resolve(false);
        };

        audio.play().catch((err) => {
          devWarn('Error al reproducir:', err);
          URL.revokeObjectURL(audioUrl);
          resolve(false);
        });
      });
    } else {
      devWarn('No se recibiÃ³ audio del backend');
      return false;
    }
  } catch (error) {
    devError('Error en TTS:', error);
    return false;
  }
};

// ===== STT (Speech-to-Text) con Google Cloud =====

export interface STTResponse {
  text: string;
  success: boolean;
}

export const recognizeSpeech = async (audioBlob: Blob): Promise<string | null> => {
  try {
    const formData = new FormData();
    const extension = 'webm';
    formData.append('audio', audioBlob, 'recording.' + extension);

    const response = await api.post<STTResponse>('/stt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    if (response.data.success && response.data.text) {
      return response.data.text;
    } else {
      devWarn('No se reconociÃ³ texto:', response.data);
      return null;
    }
  } catch (error) {
    devError('Error en STT:', error);
    return null;
  }
};

// ===== ESTADO DEL SISTEMA =====

export interface SystemStatus {
  isConnected: boolean;
  isRecording: boolean;
  isSpeaking: boolean;
  lastError: string | null;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'offline';
}

export const getSystemStatus = async (): Promise<SystemStatus> => {
  try {
    const [status, greeting] = await Promise.all([
      getStatus(),
      getGreeting().catch(() => ({ ready: false, text: null })),
    ]);

    let quality: 'excellent' | 'good' | 'poor' | 'offline' = 'offline';
    if (status.status === 'online') {
      if (status.modules.voice) quality = 'excellent';
      else if (status.modules.email) quality = 'good';
      else quality = 'poor';
    }

    return {
      isConnected: status.status === 'online',
      isRecording: false,
      isSpeaking: greeting.ready,
      lastError: null,
      connectionQuality: quality,
    };
  } catch (error) {
    devError('Error obteniendo estado del sistema:', error);
    return {
      isConnected: false,
      isRecording: false,
      isSpeaking: false,
      lastError: error instanceof Error ? error.message : 'Error desconocido',
      connectionQuality: 'offline',
    };
  }
};

// ===== MENSAJES CON INDICADORES DE CARGA =====

export const sendMessageWithIndicator = async (message: string) => {
  setLoadingState(true);
  try {
    const response = await sendMessage(message);
    return { success: true, response };
  } catch (error) {
    devError('Error en envÃ­o de mensaje:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Error de conexiÃ³n' };
  } finally {
    setLoadingState(false);
  }
};

let loadingTimeout: ReturnType<typeof setTimeout> | null = null;
const setLoadingState = (loading: boolean) => {
  if (loading) {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.right = '0';
    overlay.style.bottom = '0';
    overlay.style.background = 'rgba(0,0,0,0.5)';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.zIndex = '9999';
    overlay.style.color = '#e2e8f0';
    overlay.innerHTML = `
      <div style="background: rgba(17,24,39,0.8); padding: 2rem; border-radius: 16px; text-align: center;">
        <div style="font-size: 48px; margin-bottom: 1rem;">â³</div>
        <div style="font-size: 14px; margin-bottom: 0.5rem;">PROCESANDO...</div>
        <div style="font-size: 12px; color: rgba(147,197,253,0.5);">Por favor espere</div>
      </div>
    `;
    document.body.appendChild(overlay);
  } else {
    if (loadingTimeout) {
      clearTimeout(loadingTimeout);
      loadingTimeout = null;
    }
    const overlay = document.querySelector('div[style*="fixed"][style*="9999"]');
    if (overlay) {
      overlay.remove();
    }
  }
};

// ===== COMANDOS ESPECIALES =====

export const parseNewsResponse = (text: string): any[] => {
  const articles: any[] = [];
  const lines = text.split('\n');
  let currentArticle: any = {};

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.match(/^\*\*\d+\.\s/)) {
      if (currentArticle.title) articles.push(currentArticle);
      currentArticle = { title: line.replace(/^\*\*\d+\.\s/, '').replace(/\*\*$/, '') };
    } else if (line.startsWith('ðŸ“Œ *Fuente:*')) {
      currentArticle.source = line.replace('ðŸ“Œ *Fuente:*', '').trim();
      currentArticle.source_name = currentArticle.source;
    } else if (line.startsWith('ðŸ·ï¸ *CategorÃ­a:*')) {
      currentArticle.category = line.replace('ðŸ·ï¸ *CategorÃ­a:*', '').split(',').map((c: string) => c.trim());
    } else if (line.startsWith('ðŸ“ ')) {
      currentArticle.description = line.replace('ðŸ“ ', '');
    }
  }
  if (currentArticle.title) articles.push(currentArticle);
  return articles;
};

export const searchNews = async (topic: string): Promise<any[]> => {
  try {
    const response = await sendMessage('buscar noticias ' + topic);
    return parseNewsResponse(response.response);
  } catch (error) {
    devError('Error buscando noticias:', error);
    return [];
  }
};

export const formatNewsForWhatsApp = (articles: any[]): string => {
  if (!articles || articles.length === 0) return 'No hay noticias disponibles';

  let message = 'ðŸ“° *Resumen de Noticias*\n\n';
  articles.slice(0, 5).forEach((article, index) => {
    const title = article.title || 'Sin tÃ­tulo';
    const description = article.description || 'Sin descripciÃ³n';
    const source = article.source_name || 'Fuente desconocida';
    const date = article.published_at ? new Date(article.published_at).toLocaleDateString('es-ES') : 'Hoy';

    message += (index + 1) + '. *' + title + '*\n';
    message += '   ðŸ“ ' + description.substring(0, 100) + (description.length > 100 ? '...' : '') + '\n';
    message += '   ðŸ“Ž ' + source + ' â€¢ ' + date + '\n\n';
  });

  return message;
};

// Interfaz para el response del chat
export interface ChatResponse {
  response: string;
  intent: string;
  action: boolean;
  navigate?: string;
}

export interface StatusResponse {
  status: string;
  version: string;
  modules: {
    notion: boolean;
    calendar: boolean;
    email: boolean;
    voice: boolean;
    data: boolean;
    telegram: boolean;
  };
}

// ===== VOZ (Google TTS via Backend) =====

export interface SpeakResponse {
  audio: string;
  format: string;
}

// ===== CLIMA =====

// ===== BÃ“VEDA (memoria en Markdown) =====

export interface VaultGraphNode {
  id: string;
  title: string;
  path: string;
}

export interface VaultGraphEdge {
  source: string;
  target: string;
}

export interface VaultGraphResponse {
  nodes: VaultGraphNode[];
  edges: VaultGraphEdge[];
}

export interface VaultStats {
  raw_count: number;
  wiki_count: number;
  outputs_count: number;
  graph_nodes: number;
  graph_edges: number;
}

export const getVaultGraph = async (): Promise<VaultGraphResponse> => {
  const response = await api.get<VaultGraphResponse>('/vault/graph');
  return response.data;
};

export const getVaultStats = async (): Promise<VaultStats> => {
  const response = await api.get<VaultStats>('/vault/stats');
  return response.data;
};

export interface VaultNote {
  name: string;
  path: string;
  modified: string;
  size_bytes: number;
}

export const getVaultNotes = async (layer: "raw" | "wiki" | "outputs"): Promise<VaultNote[]> => {
  const response = await api.get<{ layer: string; notes: VaultNote[] }>(`/vault/notes?layer=${layer}`);
  return response.data.notes;
};

// ===== SISTEMA (CPU / RAM / disco reales) =====

export interface SystemStats {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  disk_used_gb: number;
  disk_total_gb: number;
}

export const getSystemStats = async (): Promise<SystemStats> => {
  const response = await api.get<SystemStats>('/system');
  return response.data;
};

// ===== TAREAS (Notion) Y EVENTOS (Calendar) =====

export interface TaskItem {
  title: string;
}

export const getTasksList = async (): Promise<TaskItem[]> => {
  const response = await api.get<{ tasks: TaskItem[] }>('/tasks/list');
  return response.data.tasks;
};

export interface EventItem {
  title: string;
  time: string;
}

export const getEventsToday = async (): Promise<EventItem[]> => {
  const response = await api.get<{ events: EventItem[] }>('/events/today');
  return response.data.events;
};

// ===== NOTICIAS (estructurado) =====

export interface Headline {
  title: string;
  description: string;
  source: string;
  source_name: string;
  url: string;
  published_at: string;
  image: string;
  category: string[];
}

export const getNewsHeadlines = async (category?: string, limit = 8): Promise<{ articles: Headline[]; available: boolean }> => {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  params.set("limit", String(limit));
  const response = await api.get<{ articles: Headline[]; available: boolean }>(`/news/headlines?${params.toString()}`);
  return response.data;
};

// ===== BITCOIN =====

export interface BitcoinPrice {
  usd: number;
  clp: number;
  usd_24h_change: number;
  last_updated_at: number;
}

export const getBitcoinPrice = async (): Promise<BitcoinPrice> => {
  const response = await api.get<BitcoinPrice>('/crypto/bitcoin');
  return response.data;
};

// ===== YOUTUBE SEARCH =====

export interface YouTubeVideo {
  id: string;
  title: string;
  channel: string;
  thumbnail: string;
  published: string;
}

export const searchYouTube = async (query: string, maxResults = 5): Promise<YouTubeVideo[]> => {
  const response = await api.get<{ videos: YouTubeVideo[]; query: string }>('/youtube/search', {
    params: { q: query, max_results: maxResults },
  });
  return response.data.videos;
};

// ===== LEVEL 4: PRIVACY / VISION / EVENTS =====

export interface PrivacyState {
  camera_enabled: boolean;
  microphone_enabled: boolean;
  location_enabled: boolean;
  ambient_sensors: boolean;
  auto_save_images: boolean;
}

export const getPrivacy = async (): Promise<PrivacyState> => {
  const response = await api.get<PrivacyState>('/privacy');
  return response.data;
};

export const setPrivacy = async (feature: string, enabled?: boolean): Promise<{ state: PrivacyState; killed?: number; restored?: number }> => {
  const payload = enabled !== undefined ? { feature, enabled } : { feature };
  const response = await api.post('/privacy', payload);
  return response.data;
};

export interface VisionStatus {
  camera: { available: boolean; last_capture: unknown; opencv: boolean };
  vision_model: boolean;
}

export interface VisionCapture {
  captured: boolean;
  simulated: boolean;
  description: string | null;
  timestamp: string | null;
}

export const getVisionStatus = async (): Promise<VisionStatus> => {
  const response = await api.get<VisionStatus>('/vision/status');
  return response.data;
};

export const captureVision = async (question?: string): Promise<VisionCapture> => {
  const response = await api.post<VisionCapture>('/vision/capture', { question: question || 'Que hay en esta imagen?' });
  return response.data;
};

export interface EventItem2 {
  name: string;
  data: Record<string, unknown>;
  source: string;
  timestamp: number;
}

export const getEvents = async (limit?: number): Promise<EventItem2[]> => {
  const response = await api.get<{ events: EventItem2[] }>('/events', { params: { limit: limit || 20 } });
  return response.data.events;
};

export const captureFromDevice = async (imageBase64: string, question?: string): Promise<VisionCapture> => {
  const response = await api.post<VisionCapture>('/vision/capture-device', {
    image: imageBase64,
    question: question || 'Que hay en esta imagen?',
  });
  return response.data;
};

export const publishEvent = async (name: string, data?: Record<string, unknown>): Promise<{ published: boolean; event: string }> => {
  const response = await api.post('/events', { name, data: data || {} });
  return response.data;
};

// ... resto de los exports existentes que estaban en tu archivo original
// (Send, Mic, MapPin, etc. interfaces si las tenÃ­as, pero las esenciales estÃ¡n arriba)