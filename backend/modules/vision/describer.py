# vision/describer.py - Describir imagenes con LLM multimodal
import os
import base64
from typing import Optional
import httpx

class VisionDescriber:
    def __init__(self):
        self._api_key = os.getenv("GROQ_API_KEY", "")
        self._model = os.getenv("VISION_MODEL", "llama-3.2-90b-vision-preview")
        self._base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self._available = bool(self._api_key)
        if self._available:
            print(f"[Vision] OK - modelo: {self._model}")
        else:
            print("[Vision] WARNING - GROQ_API_KEY no configurada")

    @property
    def is_available(self) -> bool:
        return self._available

    def describe(self, image_path: str, question: str = "Que hay en esta imagen?") -> Optional[str]:
        if not self._available:
            return None
        try:
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower().lstrip(".")
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
            mime = mime_map.get(ext, "image/jpeg")
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "Sos Saturday. Describe lo que ves de forma clara y concisa en espanol."},
                    {"role": "user", "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_data}"}}
                    ]}
                ],
                "max_tokens": 512,
                "temperature": 0.3,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{self._base_url}/chat/completions", json=payload,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"})
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[Vision] ERROR: {e}")
            return None

    def describe_bytes(self, image_bytes: bytes, question: str = "Que hay en esta imagen?") -> Optional[str]:
        if not self._available:
            return None
        try:
            img_data = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "Sos Saturday. Describe lo que ves de forma clara y concisa en espanol."},
                    {"role": "user", "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                    ]}
                ],
                "max_tokens": 512,
                "temperature": 0.3,
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(f"{self._base_url}/chat/completions", json=payload,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._api_key}"})
                resp.raise_for_status()
                result = resp.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[Vision] ERROR: {e}")
            return None
