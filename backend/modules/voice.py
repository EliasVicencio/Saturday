# modules/voice.py - VERSIÓN COMPLETA CON CONVERSIÓN
import os
import base64
import requests
import tempfile
import subprocess
import platform
from typing import Optional, Tuple

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️ speech_recognition no disponible")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    print("✅ pydub disponible")
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ pydub no disponible (instalar: pip install pydub)")

class VoiceManager:
    """Gestor de voz para Saturday (TTS + STT)"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.voice_name = os.getenv("SATURDAY_VOICE", "es-ES-Chirp3-HD-Charon")
        self.language_code = os.getenv("SATURDAY_LANGUAGE", "es-ES")
        self.use_google = bool(self.api_key)
        
        print(f"🔑 API Key: {self.api_key[:10] if self.api_key else 'NO'}...")
        print(f"🎤 Voz TTS: {self.voice_name}")
        print(f"🌐 Idioma: {self.language_code}")
        print(f"📡 Google TTS: {'HABILITADO' if self.use_google else 'DESHABILITADO'}")
        print(f"📡 Google STT: {'HABILITADO' if self.use_google else 'DESHABILITADO'}")
        
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
        
        # STT - Solo si speech_recognition está disponible
        self.recognizer = None
        self.microphone = None
        self.stt_available = False
        
        if SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.stt_available = True
                print("✅ Micrófono calibrado")
            except Exception as e:
                print(f"⚠️ Error inicializando micrófono: {e}")
                self.stt_available = False
        else:
            print("⚠️ speech_recognition no disponible")
    
    # ============ TTS (Text-to-Speech) ============
    
    def speak(self, text: str) -> bool:
        """Sintetiza y reproduce texto usando Google TTS o fallback local"""
        if not text:
            return False
        
        print(f"🗣️ Speaking: {text[:50]}...")
        
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
        """Sintetiza texto usando Google Cloud TTS API"""
        if not self.api_key:
            print("⚠️ No hay API key de Google")
            return None
        
        url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": self.language_code,
                "name": self.voice_name
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 0.9,
                "pitch": 0,
                "volumeGainDb": 0
            }
        }
        
        try:
            print(f"📤 Enviando a Google TTS: {self.voice_name}")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️ Error en Google TTS: {response.status_code}")
                print(f"   {response.text[:200]}")
                return None
            
            data = response.json()
            audio_content = data.get("audioContent")
            if audio_content:
                print(f"✅ Audio generado ({len(audio_content)} caracteres base64)")
                return base64.b64decode(audio_content)
            else:
                print("⚠️ No se recibió contenido de audio")
                return None
                
        except requests.exceptions.Timeout:
            print("⚠️ Timeout en Google TTS")
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
    
    # ============ STT (Speech-to-Text) con Google Cloud ============
    
    def convert_to_wav(self, input_path: str) -> Optional[str]:
        """Convierte cualquier audio a WAV (16kHz, mono, 16-bit)"""
        if not PYDUB_AVAILABLE:
            print("⚠️ pydub no disponible, no se puede convertir")
            return None
        
        try:
            print(f"🔄 Convirtiendo {input_path} a WAV...")
            
            # Cargar audio (auto-detectar formato)
            audio = AudioSegment.from_file(input_path)
            
            # Convertir a WAV (16kHz, mono, 16-bit)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Guardar como WAV temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                output_path = tmp_wav.name
                audio.export(output_path, format="wav")
                print(f"✅ Convertido a: {output_path}")
                return output_path
                
        except Exception as e:
            print(f"⚠️ Error convirtiendo audio: {e}")
            return None
    
    # modules/voice.py - Método recognize_audio_file corregido

    def recognize_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Reconoce voz desde un archivo de audio
        Soporta: WAV, WEBM, MP3, OGG, etc.
        """
        if not self.api_key:
            print("⚠️ No hay API key de Google")
            return None
        
        try:
            # SIEMPRE intentar convertir a WAV con pydub si está disponible
            wav_path = None
            
            if PYDUB_AVAILABLE:
                try:
                    print(f"🔄 Forzando conversión de {audio_path} a WAV...")
                    
                    # Cargar audio (auto-detectar formato)
                    audio = AudioSegment.from_file(audio_path)
                    
                    # Convertir a WAV (16kHz, mono, 16-bit)
                    audio = audio.set_frame_rate(16000)
                    audio = audio.set_channels(1)
                    audio = audio.set_sample_width(2)  # 16-bit
                    
                    # Guardar como WAV temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                        wav_path = tmp_wav.name
                        audio.export(wav_path, format="wav")
                        print(f"✅ Convertido a WAV: {wav_path}")
                    
                    # Usar el archivo convertido
                    audio_path_to_use = wav_path
                    
                except Exception as e:
                    print(f"⚠️ Error en conversión: {e}")
                    print("   Intentando con el archivo original...")
                    audio_path_to_use = audio_path
            else:
                print("⚠️ pydub no disponible, usando archivo original")
                audio_path_to_use = audio_path
            
            # Leer el archivo de audio
            with open(audio_path_to_use, "rb") as f:
                audio_data = f.read()
            
            # Codificar en base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            url = "https://speech.googleapis.com/v1/speech:recognize"
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Configuración para WAV (LINEAR16)
            payload = {
                "config": {
                    "encoding": "LINEAR16",
                    "sampleRateHertz": 16000,
                    "languageCode": self.language_code,
                    "enableAutomaticPunctuation": True,
                    "model": "latest_long",
                    "useEnhanced": True,
                    "audioChannelCount": 1
                },
                "audio": {
                    "content": audio_base64
                }
            }
            
            print(f"📤 Enviando a Google STT...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Si falla, intentar con configuración automática
            if response.status_code == 400 and "sample_rate_hertz" in response.text:
                print("🔄 Intentando con configuración automática...")
                # Quitar sampleRateHertz para que Google lo detecte automáticamente
                del payload["config"]["sampleRateHertz"]
                response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"⚠️ Error en Google STT: {response.status_code}")
                print(f"   {response.text[:300]}")
                return None
            
            data = response.json()
            
            if "results" in data and data["results"]:
                transcript = data["results"][0].get("alternatives", [{}])[0].get("transcript", "")
                print(f"📝 Texto reconocido: '{transcript}'")
                return transcript.strip()
            
            print("⚠️ No se reconoció texto")
            return None
            
        except Exception as e:
            print(f"⚠️ Error en Google STT: {e}")
            return None
        finally:
            # Limpiar archivos temporales
            try:
                if wav_path and os.path.exists(wav_path) and wav_path != audio_path:
                    os.unlink(wav_path)
            except:
                pass
    
    def listen_google(self, timeout: int = 5) -> Tuple[bool, str]:
        """Escucha y reconoce voz usando Google Cloud STT"""
        if not self.stt_available:
            print("⚠️ STT no disponible")
            return False, ""
        
        print(f"🎤 Escuchando (Google STT)...")
        
        try:
            import tempfile
            import wave
            
            # Grabar audio desde el micrófono
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Guardar el audio en un archivo temporal WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_path = tmp_file.name
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio.get_wav_data())
            
            # Reconocer con Google STT
            text = self.recognize_audio_file(tmp_path)
            
            if text:
                return True, text
            else:
                return False, ""
                
        except sr.WaitTimeoutError:
            print("⏰ Tiempo de espera agotado")
            return False, ""
        except Exception as e:
            print(f"❌ Error al escuchar: {e}")
            return False, ""
    
    def listen(self, timeout: int = 5) -> Tuple[bool, str]:
        """Escucha y reconoce voz usando el método disponible"""
        # Intentar con Google STT
        if self.use_google and self.stt_available:
            try:
                return self.listen_google(timeout)
            except Exception as e:
                print(f"⚠️ Error en Google STT, usando fallback: {e}")
        
        # Fallback: speech_recognition local
        if self.stt_available:
            try:
                print(f"🎤 Escuchando (fallback local)...")
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
        
        print("⚠️ No hay método de reconocimiento de voz disponible")
        return False, ""

    def recognize_webm_file(self, audio_path: str) -> Optional[str]:
        """Método legacy para compatibilidad"""
        return self.recognize_audio_file(audio_path)