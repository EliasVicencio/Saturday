# modules/voice.py
import os
import base64
import requests
import tempfile
import subprocess
import platform
import speech_recognition as sr
from typing import Optional, Tuple, Callable

class VoiceManager:
    """Gestor de voz para Saturday (TTS + STT)"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.voice_name = os.getenv("SATURDAY_VOICE", "es-ES-Chirp3-HD-Charon")
        self.language_code = os.getenv("SATURDAY_LANGUAGE", "es-ES")
        self.use_google = bool(self.api_key)
        
        # TTS local (fallback)
        self.local_engine = None
        try:
            import pyttsx3
            self.local_engine = pyttsx3.init()
            self.local_engine.setProperty('rate', 170)
            self.local_engine.setProperty('volume', 0.9)
            print("✅ TTS local inicializado")
        except Exception as e:
            print(f"⚠️ Error inicializando TTS local: {e}")
        
        # STT
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Micrófono calibrado")
        except Exception as e:
            print(f"⚠️ Error calibrando micrófono: {e}")
    
    def speak(self, text: str) -> bool:
        """Sintetiza y reproduce texto usando Google TTS o fallback local"""
        if not text:
            return False
        
        # Google TTS
        if self.use_google:
            try:
                audio_data = self._synthesize_google_tts(text)
                if audio_data:
                    self._play_audio(audio_data)
                    return True
            except Exception as e:
                print(f"⚠️ Error en Google TTS: {e}")
        
        # Fallback local
        if self.local_engine:
            try:
                self.local_engine.say(text)
                self.local_engine.runAndWait()
                return True
            except Exception as e:
                print(f"❌ Error en TTS local: {e}")
                return False
        
        print(f"📝 Saturday (texto): {text}")
        return False
    
    def _synthesize_google_tts(self, text: str) -> Optional[bytes]:
        if not self.api_key:
            return None
        
        url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": self.language_code, "name": self.voice_name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code != 200:
                return None
            audio_content = response.json().get("audioContent")
            if audio_content:
                return base64.b64decode(audio_content)
            return None
        except Exception as e:
            print(f"⚠️ Error en Google TTS: {e}")
            return None
    
    def _play_audio(self, audio_data: bytes) -> bool:
        try:
            import time
            import threading
            filename = f"temp_audio_{int(time.time())}.mp3"
            with open(filename, "wb") as f:
                f.write(audio_data)
            
            system = platform.system()
            if system == "Windows":
                os.system(f'start "" "{filename}"')
            elif system == "Darwin":
                subprocess.Popen(["afplay", filename])
            else:
                subprocess.Popen(["mpg123", filename])
            
            def cleanup():
                time.sleep(5)
                try:
                    os.unlink(filename)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
            return True
        except Exception as e:
            print(f"⚠️ Error reproduciendo audio: {e}")
            return False
    
    def listen(self, timeout: int = 5) -> Tuple[bool, str]:
        """Escucha y reconoce voz"""
        print("🎤 Escuchando...")
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            try:
                text = self.recognizer.recognize_google(audio, language=self.language_code)
                print(f"📝 Escuché: '{text}'")
                return True, text
            except sr.UnknownValueError:
                print("❌ No entendí lo que dijiste")
                return False, ""
            except sr.RequestError:
                print("❌ Error de conexión con el servicio de reconocimiento")
                return False, ""
        except sr.WaitTimeoutError:
            print("⏰ Tiempo de espera agotado")
            return False, ""
        except Exception as e:
            print(f"❌ Error al escuchar: {e}")
            return False, ""