# 🟣 SATURDAY - Asistente Personal Inteligente

> Asistente estilo Jarvis con integración a Notion, Google Calendar, Gmail, Spotify, WhatsApp y Telegram.

---

## 🚀 Tecnologías

### Backend
- **Python 3.10+** + **Flask** (API RESTful)
- **Google Cloud TTS/STT** (Voz Charon y reconocimiento)
- **Notion API** | **Google Calendar API** | **Gmail API**
- **Spotify Web API** | **Telegram Bot API** | **CallMeBot** (WhatsApp)

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** + **Framer Motion** (Animaciones)

---

## ⚙️ Instalación Rápida

```bash
# 1. Clonar
git clone https://github.com/EliasVicencio/Saturday.git
cd Saturday

# 2. Backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Frontend
cd frontend
npm install

# 4. Variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar
# Terminal 1 - Backend
python backend/app.py

# Terminal 2 - Frontend
cd frontend && npm run dev
```
## 🔑 Credenciales Necesarias

```bash
Servicio	Dónde obtener	Variables .env
Notion	my-integrations	NOTION_API_KEY, NOTION_DB_ID
Google Cloud	Console	GOOGLE_API_KEY
Spotify	Developer Dashboard	SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
WhatsApp	CallMeBot (+34 644 51 95 23)	WHATSAPP_NUMBER, WHATSAPP_API_KEY
Telegram	@BotFather	TELEGRAM_BOT_TOKEN
OpenWeather	OpenWeatherMap	WEATHER_API_KEY
```

---
| Desarrollado por Elias Vicencio 