# audio/tts.py - Text-to-Speech module
import os
import tempfile
from typing import Optional
import httpx

class TTSEngine:
    """TTS via Google Cloud Text-to-Speech."""
    def __init__(self, api_key: str = "", voice: str = "", language: str = ""):
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._voice = voice or os.getenv("SATURDAY_VOICE", "es-ES-Chirp3-HD-Charon")
        self._language = language or os.getenv("SATURDAY_LANGUAGE", "es-ES")
        self._available = bool(self._api_key)
        if self._available:
            print(f"[TTS] OK - Google TTS ({self._voice})")
        else:
            print("[TTS] WARNING - GOOGLE_API_KEY no configurada")

    @property
    def is_available(self) -> bool:
        return self._available

    def synthesize(self, text: str) -> Optional[bytes]:
        if not self._available:
            return None
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self._api_key}"
            payload = {
                "input": {"text": text},
                "voice": {"languageCode": self._language, "name": self._voice},
                "audioConfig": {"audioEncoding": "MP3"},
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                import base64
                return base64.b64decode(data["audioContent"])
        except Exception as e:
            print(f"[TTS] ERROR: {e}")
        return None
