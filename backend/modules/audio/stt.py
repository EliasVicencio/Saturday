# audio/stt.py - Speech-to-Text module
import os
import tempfile
from typing import Optional
import httpx

class STTEngine:
    """STT via Google Cloud Speech-to-Text."""
    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self._available = bool(self._api_key)
        if self._available:
            print("[STT] OK - Google Speech-to-Text")
        else:
            print("[STT] WARNING - GOOGLE_API_KEY no configurada")

    @property
    def is_available(self) -> bool:
        return self._available

    def transcribe(self, audio_bytes: bytes, language: str = "es-ES") -> Optional[str]:
        if not self._available:
            return None
        try:
            import base64
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            url = f"https://speech.googleapis.com/v1/speech:recognize?key={self._api_key}"
            payload = {
                "config": {"encoding": "WEBM_OPUS", "sampleRateHertz": 48000, "languageCode": language},
                "audio": {"content": audio_b64},
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                if results:
                    return results[0]["alternatives"][0]["transcript"]
        except Exception as e:
            print(f"[STT] ERROR: {e}")
        return None
