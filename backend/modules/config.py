# config.py - Configuracion centralizada de Saturday
import os
from dataclasses import dataclass

@dataclass
class Config:
    # API Keys
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    vision_model: str = "llama-3.2-90b-vision-preview"
    saturday_api_key: str = ""
    google_api_key: str = ""
    weather_api_key: str = ""
    newsdata_api_key: str = ""
    youtube_api_key: str = ""
    notion_api_key: str = ""
    notion_db_id: str = ""
    telegram_bot_token: str = ""
    whatsapp_number: str = ""
    whatsapp_api_key: str = ""

    # App
    saturday_city: str = "Santiago,CL"
    saturday_language: str = "es-ES"
    saturday_voice: str = "es-ES-Chirp3-HD-Charon"
    saturday_timezone: str = "America/Santiago"
    port: int = 5000
    vite_api_url: str = ""

    # Limits
    max_history: int = 20
    max_memory_results: int = 10
    checkpoint_ttl: int = 86400

    @classmethod
    def from_env(cls):
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            groq_base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            vision_model=os.getenv("VISION_MODEL", "llama-3.2-90b-vision-preview"),
            saturday_api_key=os.getenv("SATURDAY_API_KEY", ""),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            weather_api_key=os.getenv("WEATHER_API_KEY", ""),
            newsdata_api_key=os.getenv("NEWSDATA_API_KEY", ""),
            youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
            notion_api_key=os.getenv("NOTION_API_KEY", ""),
            notion_db_id=os.getenv("NOTION_DB_ID", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            whatsapp_number=os.getenv("WHATSAPP_NUMBER", ""),
            whatsapp_api_key=os.getenv("WHATSAPP_API_KEY", ""),
            saturday_city=os.getenv("SATURDAY_CITY", "Santiago,CL"),
            saturday_language=os.getenv("SATURDAY_LANGUAGE", "es-ES"),
            saturday_voice=os.getenv("SATURDAY_VOICE", "es-ES-Chirp3-HD-Charon"),
            saturday_timezone=os.getenv("SATURDAY_TIMEZONE", "America/Santiago"),
            port=int(os.getenv("PORT", "5000")),
            vite_api_url=os.getenv("VITE_API_URL", ""),
        )

config = Config.from_env()
