// frontend/src/services/api.ts
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  };
}

export interface SpeakResponse {
  audio: string;
  format: string;
}

export const sendMessage = async (message: string): Promise<ChatResponse> => {
  const response = await api.post('/chat', { message });
  return response.data;
};

export const getStatus = async (): Promise<StatusResponse> => {
  const response = await api.get('/status');
  return response.data;
};

// ===== GOOGLE TTS VOZ (CHARON) =====
export const speakText = async (text: string): Promise<boolean> => {
  if (!text) return false;

  console.log(`🎤 Generando voz Google Charon para: "${text.substring(0, 30)}..."`);

  try {
    const response = await api.post<SpeakResponse>('/speak', { text });
    const data = response.data;

    if (data.audio) {
      console.log('✅ Audio recibido, reproduciendo...');
      
      // Decodificar base64 y reproducir
      const audioBytes = Uint8Array.from(atob(data.audio), (c) => c.charCodeAt(0));
      const audioBlob = new Blob([audioBytes], { type: 'audio/mp3' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      
      // Crear promesa para manejar la reproducción
      return new Promise((resolve) => {
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          resolve(true);
        };
        
        audio.onerror = (e) => {
          console.warn('⚠️ Error reproduciendo audio:', e);
          URL.revokeObjectURL(audioUrl);
          resolve(false);
        };
        
        // Intentar reproducir
        audio.play().catch((err) => {
          console.warn('⚠️ Error al reproducir:', err);
          resolve(false);
        });
      });
    } else {
      console.warn('⚠️ No se recibió audio');
      return false;
    }
  } catch (error) {
    console.error('❌ Error en TTS:', error);
    return false;
  }
};