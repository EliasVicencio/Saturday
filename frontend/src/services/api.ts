import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const API_BASE_URL = API_URL;

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// NUEVA INTERFACIÓN CON 'id' PARA SOLUCIONAR ERROR TYPEScRIPT
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
// Intenta extraer título de: **1. Título**, **Título**, 1. Título
function extractTitleFromLine(line: string): string | null {
  // Patrón 1: **1. Título** (número + punto + texto)
  const p1 = /^\*\*(\d+)\.\s(.+?)\*\*$/;
  const m1 = line.match(p1);
  if (m1) return m1[2];
  
  // Patrón 2: **Título** (solo negrita, sin número)
  const p2 = /^\*\*(.+?)\*\*$/;
  const m2 = line.match(p2);
  if (m2) return m2[1];
  
  // Patrón 3: 1. Título (sin negrita, solo número + punto + texto)
  const p3 = /^(\d+)\.\s(.+)$/;
  const m3 = line.match(p3);
  if (m3) return m3[2];
  
  return null;
}

// ===== FUNCIÓN PRINCIPAL GETNEWSPANEL =====
export const getNewsPanel = async (): Promise<NewsPanelData> => {
  try {
    const response = await api.get<{ response?: string; success?: boolean }>('/news');
    if (response.data.response) {
      const articles: NewsItem[] = [];
      const lines = response.data.response.split('\n');
      let currentTitle = '';
      let currentSource = '';
      
      for (const line of lines) {
        // 1. Intentar extraer título con cualquiera de los 3 patrones
        const title = extractTitleFromLine(line);
        
        if (title) {
          // Guardar título anterior antes de empezar el nuevo
          if (currentTitle) {
            articles.push({ id: `${articles.length + 1}`, title: currentTitle, description: '', source: currentSource });
          }
          currentTitle = title;
          currentSource = '';
        }
        // Detectar fuente: debe contener "📌 *Fuente:*"
        else if (line.includes('📌 *Fuente:*')) {
          const sm = line.match(/📌 \*Fuente:\*\s(.+)/);
          if (sm) currentSource = sm[1];
        }
        // Detectar descripción: "📝 Texto" (opcional, se ignora por simplicidad)
        else if (line.startsWith('📝 ')) {
          // Se asocia descriptivamente al título actual (ignoramos por simplicidad)
        }
      }
      // Empujar el último título si quedó pendiente
      if (currentTitle) {
        articles.push({ id: `${articles.length + 1}`, title: currentTitle, description: '', source: currentSource });
      }
      
      return { headlines: articles, lastUpdate: new Date().toLocaleString() };
    }
    return { headlines: [], lastUpdate: 'Nunca' };
  } catch (error) {
    console.error('Error obteniendo panel de noticias:', error);
    return { headlines: [], lastUpdate: 'Error' };
  }
};

// ===== FUNCIÓN GETWEATHER (OBLIGATORIA PARA Home.tsx) =====
export const getWeather = async (): Promise<WeatherResponse> => {
  const response = await api.get<WeatherResponse>('/weather');
  return response.data;
};

// ===== ENVÍO DE MENSAJES =====

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
          console.warn('Error reproduciendo audio:', e);
          URL.revokeObjectURL(audioUrl);
          resolve(false);
        };

        audio.play().catch((err) => {
          console.warn('Error al reproducir:', err);
          URL.revokeObjectURL(audioUrl);
          resolve(false);
        });
      });
    } else {
      console.warn('No se recibió audio del backend');
      return false;
    }
  } catch (error) {
    console.error('Error en TTS:', error);
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
      console.warn('No se reconoció texto:', response.data);
      return null;
    }
  } catch (error) {
    console.error('Error en STT:', error);
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
    console.error('Error obteniendo estado del sistema:', error);
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
    console.error('Error en envío de mensaje:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Error de conexión' };
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
        <div style="font-size: 48px; margin-bottom: 1rem;">⏳</div>
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
    } else if (line.startsWith('📌 *Fuente:*')) {
      currentArticle.source = line.replace('📌 *Fuente:*', '').trim();
      currentArticle.source_name = currentArticle.source;
    } else if (line.startsWith('🏷️ *Categoría:*')) {
      currentArticle.category = line.replace('🏷️ *Categoría:*', '').split(',').map((c: string) => c.trim());
    } else if (line.startsWith('📝 ')) {
      currentArticle.description = line.replace('📝 ', '');
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
    console.error('Error buscando noticias:', error);
    return [];
  }
};

export const formatNewsForWhatsApp = (articles: any[]): string => {
  if (!articles || articles.length === 0) return 'No hay noticias disponibles';

  let message = '📰 *Resumen de Noticias*\n\n';
  articles.slice(0, 5).forEach((article, index) => {
    const title = article.title || 'Sin título';
    const description = article.description || 'Sin descripción';
    const source = article.source_name || 'Fuente desconocida';
    const date = article.published_at ? new Date(article.published_at).toLocaleDateString('es-ES') : 'Hoy';

    message += (index + 1) + '. *' + title + '*\n';
    message += '   📝 ' + description.substring(0, 100) + (description.length > 100 ? '...' : '') + '\n';
    message += '   📎 ' + source + ' • ' + date + '\n\n';
  });

  return message;
};

// Interfaz para el response del chat
export interface ChatResponse {
  response: string;
  intent: string;
  action: boolean;
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

// ... resto de los exports existentes que estaban en tu archivo original
// (Send, Mic, MapPin, etc. interfaces si las tenías, pero las esenciales están arriba)