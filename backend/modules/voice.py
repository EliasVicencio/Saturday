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


def _configure_ffmpeg_path():
    """
    Busca ffmpeg/ffprobe y se los indica a pydub explícitamente, sin
    depender de que el PATH del proceso de Python (que puede venir
    'cacheado' de una terminal vieja, VS Code, un launcher, etc.) esté
    actualizado. Si no encuentra nada, no hace nada (pydub seguirá
    intentando 'ffmpeg' a secas, como antes).
    """
    if not PYDUB_AVAILABLE:
        return

    import shutil

    # 1. Permitir que el usuario fije la ruta manualmente en el .env
    #    si por algún motivo la auto-detección no funciona.
    manual_dir = os.getenv("FFMPEG_DIR")

    candidates_dirs = []
    if manual_dir:
        candidates_dirs.append(manual_dir)

    # 2. Rutas típicas donde queda instalado ffmpeg en Windows/Linux/Mac
    #    cuando se sigue la guía de instalación manual (zip descomprimido).
    candidates_dirs += [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
        "/usr/local/bin",
        "/opt/homebrew/bin",
    ]

    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")

    if not ffmpeg_path or not ffprobe_path:
        for d in candidates_dirs:
            exe = ".exe" if platform.system() == "Windows" else ""
            candidate_ffmpeg = os.path.join(d, f"ffmpeg{exe}")
            candidate_ffprobe = os.path.join(d, f"ffprobe{exe}")
            if not ffmpeg_path and os.path.isfile(candidate_ffmpeg):
                ffmpeg_path = candidate_ffmpeg
            if not ffprobe_path and os.path.isfile(candidate_ffprobe):
                ffprobe_path = candidate_ffprobe
            if ffmpeg_path and ffprobe_path:
                break

    if ffmpeg_path:
        AudioSegment.converter = ffmpeg_path
        print(f"🎬 ffmpeg encontrado en: {ffmpeg_path}")
    else:
        print("⚠️ No se encontró ffmpeg (ni en PATH ni en rutas típicas). "
              "Si ya lo instalaste, poné la carpeta 'bin' en la variable "
              "FFMPEG_DIR del .env, ej: FFMPEG_DIR=C:\\ffmpeg\\bin")

    if ffprobe_path:
        AudioSegment.ffprobe = ffprobe_path
        print(f"🔎 ffprobe encontrado en: {ffprobe_path}")
    else:
        print("⚠️ No se encontró ffprobe (ni en PATH ni en rutas típicas).")


_configure_ffmpeg_path()

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
        
        print(f"🗣️ Saturday: {text}")
        
        # Intentar con Google TTS
        if self.use_google:
            try:
                audio_data = self._synthesize_google_tts(text)
                if audio_data:
                    self._play_audio(audio_data)
                    return True
                else:
                    print("⚠️ Google TTS no generó audio, usando fallback local")
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
        
        # Último recurso: solo imprimir
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

    def _build_stt_config(self, audio_path: str, converted_to_wav: bool, use_enhanced: bool = False) -> dict:
        """Arma el bloque 'config' de Google STT según el formato real del archivo."""
        ext = os.path.splitext(audio_path)[1].lower()

        base_config = {
            "languageCode": self.language_code,
            "enableAutomaticPunctuation": True,
            # "command_and_search" está pensado para frases cortas de comando
            # (justo lo que dice un asistente de voz), a diferencia de
            # "latest_long" que es para audio largo tipo discurso/video.
            "model": "command_and_search",
            "audioChannelCount": 1,
            # Vocabulario esperado del asistente: ayuda a Google a inclinarse
            # hacia estas palabras cuando hay ambigüedad.
            "speechContexts": [{
                "phrases": [
                    "dashboard", "proyectos", "noticias", "inicio", "tareas",
                    "clima", "hora", "Saturday", "recordatorio", "calendario",
                    "correo", "Notion", "Spotify",
                ],
                "boost": 15,
            }],
        }

        # useEnhanced pide un modelo "enhanced" que puede no estar habilitado
        # en el proyecto de Google Cloud; si no está disponible, Google no
        # tira error, simplemente devuelve resultados vacíos. Lo dejamos
        # apagado por defecto y solo se prueba explícitamente si se pide.
        if use_enhanced:
            base_config["useEnhanced"] = True

        if converted_to_wav or ext == ".wav":
            # Ya viene como WAV 16kHz/16-bit mono (convertido por pydub)
            base_config["encoding"] = "LINEAR16"
            base_config["sampleRateHertz"] = 16000
        elif ext == ".webm":
            # Audio del navegador (MediaRecorder) sin convertir: Opus dentro de WebM.
            # No hace falta ffmpeg/pydub para esto, Google lo soporta nativo.
            # La cabecera del propio archivo WebM ya indica 48000Hz.
            base_config["encoding"] = "WEBM_OPUS"
            base_config["sampleRateHertz"] = 48000
        elif ext in (".ogg", ".oga"):
            base_config["encoding"] = "OGG_OPUS"
            base_config["sampleRateHertz"] = 48000
        elif ext == ".flac":
            base_config["encoding"] = "FLAC"
        else:
            # Formato desconocido: dejar que Google intente detectar por cabecera
            base_config["encoding"] = "ENCODING_UNSPECIFIED"

        return base_config

    def recognize_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Reconoce voz desde un archivo de audio.
        Soporta WEBM/OGG (Opus, nativo del navegador) sin necesitar ffmpeg,
        y WAV/FLAC directamente. Solo convierte con pydub como último recurso
        para formatos que Google no soporta de forma nativa.
        """
        if not self.api_key:
            print("⚠️ No hay API key de Google")
            return None

        wav_path = None
        audio_path_to_use = audio_path
        converted_to_wav = False

        ext = os.path.splitext(audio_path)[1].lower()
        NATIVE_FORMATS = (".webm", ".ogg", ".oga", ".wav", ".flac")

        try:
            # 1. Solo convertir si el formato no es soportado nativamente por Google STT
            if ext not in NATIVE_FORMATS and PYDUB_AVAILABLE:
                try:
                    print(f"🔄 Formato '{ext}' no nativo, convirtiendo a WAV con pydub...")
                    audio = AudioSegment.from_file(audio_path)
                    audio = audio.set_frame_rate(16000)
                    audio = audio.set_channels(1)
                    audio = audio.set_sample_width(2)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                        wav_path = tmp_wav.name
                        audio.export(wav_path, format="wav")
                        print(f"✅ Convertido a WAV: {wav_path}")

                    audio_path_to_use = wav_path
                    converted_to_wav = True
                except Exception as e:
                    print(f"⚠️ Error en conversión (¿falta ffmpeg?): {e}")
                    print("   Se intentará mandar el archivo original tal cual.")
                    audio_path_to_use = audio_path

            # 2. Leer el archivo de audio
            with open(audio_path_to_use, "rb") as f:
                audio_data = f.read()

            # 3. Codificar en base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # DEBUG: tamaño real del audio que se manda. Un archivo webm
            # de una frase hablada normal suele pesar varias decenas de KB;
            # si esto da muy pocos bytes (ej. <3-5 KB), es señal de que el
            # clip capturado es casi vacío aunque al reproducirlo "suene"
            # a algo (Opus comprime muchísimo el silencio/ruido de fondo).
            print(f"📏 Tamaño del audio: {len(audio_data)} bytes ({len(audio_data)/1024:.1f} KB), "
                  f"base64: {len(audio_base64)} chars")

            # 4. Enviar a Google STT con la config correcta para el formato real.
            # Ya confirmamos que el sample rate (48000 para WEBM_OPUS del
            # navegador) NO es el problema: con la tasa correcta Google
            # respondía 200 OK pero sin resultados. Ahora probamos variantes
            # de MODELO en vez de sample rate.
            url = "https://speech.googleapis.com/v1/speech:recognize"
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }

            # Variantes a probar en orden: primero el modelo pensado para
            # comandos cortos (lo normal para un asistente de voz), después
            # sin modelo específico (deja que Google elija el default), y
            # por último con el modelo "enhanced" por si el proyecto sí lo
            # tiene habilitado.
            attempts = [
                {"model": "command_and_search", "use_enhanced": False},
                {"model": None, "use_enhanced": False},
                {"model": "latest_long", "use_enhanced": True},
            ]

            last_response = None
            for attempt in attempts:
                config = self._build_stt_config(
                    audio_path_to_use, converted_to_wav,
                    use_enhanced=attempt["use_enhanced"],
                )
                if attempt["model"] is None:
                    config.pop("model", None)
                else:
                    config["model"] = attempt["model"]

                payload = {"config": config, "audio": {"content": audio_base64}}
                print(f"📤 Enviando a Google STT (model={attempt['model']}, useEnhanced={attempt['use_enhanced']})...")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                last_response = response

                if response.status_code != 200:
                    print(f"⚠️ Error en Google STT: {response.status_code}")
                    print(f"   {response.text[:300]}")
                    continue

                data = response.json()
                if "results" in data and data["results"]:
                    transcript = data["results"][0].get("alternatives", [{}])[0].get("transcript", "")
                    print(f"✅ Reconocido con model={attempt['model']}: '{transcript}'")
                    return transcript.strip()

                print(f"   ⚠️ 200 OK pero sin resultados con model={attempt['model']}, probando otra variante...")

            # Último recurso: convertir a WAV con pydub/ffmpeg si no lo
            # habíamos hecho ya (requiere ffmpeg Y ffprobe instalados).
            if not converted_to_wav and PYDUB_AVAILABLE:
                try:
                    print("🔄 Ninguna variante funcionó con Opus, probando conversión a WAV como último recurso...")
                    audio = AudioSegment.from_file(audio_path)
                    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                        wav_path = tmp_wav.name
                        audio.export(wav_path, format="wav")

                    with open(wav_path, "rb") as f:
                        wav_base64 = base64.b64encode(f.read()).decode('utf-8')

                    payload = {
                        "config": {
                            "encoding": "LINEAR16",
                            "sampleRateHertz": 16000,
                            "languageCode": self.language_code,
                            "enableAutomaticPunctuation": True,
                            "model": "command_and_search",
                            "audioChannelCount": 1,
                        },
                        "audio": {"content": wav_base64},
                    }
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if "results" in data and data["results"]:
                            transcript = data["results"][0].get("alternatives", [{}])[0].get("transcript", "")
                            print(f"✅ Reconocido tras convertir a WAV: '{transcript}'")
                            return transcript.strip()
                    last_response = response
                except Exception as e:
                    print(f"⚠️ Falló también la conversión a WAV: {e}")

            if last_response is not None and last_response.status_code != 200:
                print(f"⚠️ Error final en Google STT: {last_response.status_code}")
                print(f"   {last_response.text[:300]}")
            else:
                print("⚠️ No se reconoció texto en ninguna variante probada (Google no detectó habla)")
            return None

        except Exception as e:
            print(f"⚠️ Error en Google STT: {e}")
            return None
        finally:
            try:
                if wav_path and os.path.exists(wav_path):
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