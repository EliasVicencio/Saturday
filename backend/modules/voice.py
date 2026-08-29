import logging
logger = logging.getLogger("saturday.voice")
# modules/voice.py - VERSIN COMPLETA CON CONVERSIN
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
    logger.info(" speech_recognition no disponible")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
    logger.info(" pydub disponible")
except ImportError:
    PYDUB_AVAILABLE = False
    logger.info(" pydub no disponible (instalar: pip install pydub)")


def _configure_ffmpeg_path():
    """
    Busca ffmpeg/ffprobe y se los indica a pydub explcitamente, sin
    depender de que el PATH del proceso de Python (que puede venir
    'cacheado' de una terminal vieja, VS Code, un launcher, etc.) est
    actualizado. Si no encuentra nada, no hace nada (pydub seguir
    intentando 'ffmpeg' a secas, como antes).
    """
    if not PYDUB_AVAILABLE:
        return

    import shutil

    # 1. Permitir que el usuario fije la ruta manualmente en el .env
    #    si por algn motivo la auto-deteccin no funciona.
    manual_dir = os.getenv("FFMPEG_DIR")

    candidates_dirs = []
    if manual_dir:
        candidates_dirs.append(manual_dir)

    # 2. Rutas tpicas donde queda instalado ffmpeg en Windows/Linux/Mac
    #    cuando se sigue la gua de instalacin manual (zip descomprimido).
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
        logger.info(f" ffmpeg encontrado en: {ffmpeg_path}")
    else:
        logger.info(" No se encontr ffmpeg (ni en PATH ni en rutas tpicas). "
              "Si ya lo instalaste, pon la carpeta 'bin' en la variable "
              "FFMPEG_DIR del .env, ej: FFMPEG_DIR=C:\\ffmpeg\\bin")

    if ffprobe_path:
        AudioSegment.ffprobe = ffprobe_path
        logger.info(f" ffprobe encontrado en: {ffprobe_path}")
    else:
        logger.info(" No se encontr ffprobe (ni en PATH ni en rutas tpicas).")


_configure_ffmpeg_path()

class VoiceManager:
    """Gestor de voz para Saturday (TTS + STT)"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.voice_name = os.getenv("SATURDAY_VOICE", "es-ES-Chirp3-HD-Charon")
        self.language_code = os.getenv("SATURDAY_LANGUAGE", "es-ES")
        self.use_google = bool(self.api_key)
        
        logger.info(f"API Key: {'configured' if self.api_key else 'NOT configured'}")
        logger.info(f" Voz TTS: {self.voice_name}")
        logger.info(f" Idioma: {self.language_code}")
        logger.info(f" Google TTS: {'HABILITADO' if self.use_google else 'DESHABILITADO'}")
        logger.info(f" Google STT: {'HABILITADO' if self.use_google else 'DESHABILITADO'}")
        
        # TTS local (fallback)
        self.local_engine = None
        try:
            import pyttsx3
            self.local_engine = pyttsx3.init()
            self.local_engine.setProperty('rate', 170)
            self.local_engine.setProperty('volume', 0.9)
            logger.info(" TTS local inicializado")
        except Exception as e:
            logger.info(f" Error inicializando TTS local: {e}")
        
        # STT - Solo si speech_recognition est disponible
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
                logger.info(" Micrfono calibrado")
            except Exception as e:
                logger.info(f" Error inicializando micrfono: {e}")
                self.stt_available = False
        else:
            logger.info(" speech_recognition no disponible")
    
    # ============ TTS (Text-to-Speech) ============
    
    @staticmethod
    def _fix_mojibake(text: str) -> str:
        """Fix common mojibake patterns from UTF-8/Latin-1 misinterpretation"""
        replacements = {
            '\u00c2\u00bf': '\u00bf',  # ? -> 
            '\u00c2\u00a1': '\u00a1',  # ! -> 
            '\u00c3\u00b3': '\u00f3',  # o -> ó
            '\u00c3\u00a1': '\u00e1',  # a -> á
            '\u00c3\u00a9': '\u00e9',  # e -> é
            '\u00c3\u00ad': '\u00ed',  # i -> í
            '\u00c3\u00ba': '\u00fa',  # u -> ú
            '\u00c3\u00b1': '\u00f1',  # n -> ñ
            '\u00c3\u00bc': '\u00fc',  # u -> ü
            '\u00c2': '',              # stray 
        }
        for wrong, right in replacements.items():
            text = text.replace(wrong, right)
        return text
    
    def speak(self, text: str) -> bool:
        """Sintetiza y reproduce texto usando Google TTS o fallback local"""
        if not text:
            return False
        
        text = self._fix_mojibake(text)
        logger.info(f" Saturday: {text}")
        
        # Intentar con Google TTS
        if self.use_google:
            try:
                audio_data = self._synthesize_google_tts(text)
                if audio_data:
                    self._play_audio(audio_data)
                    return True
                else:
                    logger.info(" Google TTS no gener audio, usando fallback local")
            except Exception as e:
                logger.info(f" Error en Google TTS: {e}")
        
        # Fallback local
        if self.local_engine:
            try:
                self.local_engine.say(text)
                self.local_engine.runAndWait()
                return True
            except Exception as e:
                logger.info(f" Error en TTS local: {e}")
                return False
        
        # ltimo recurso: solo imprimir
        logger.info(f" Saturday (texto): {text}")
        return False
    
    def _synthesize_google_tts(self, text: str) -> Optional[bytes]:
        """Sintetiza texto usando Google Cloud TTS API"""
        if not self.api_key:
            logger.info(" No hay API key de Google")
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
                "speakingRate": float(os.getenv("SATURDAY_TTS_RATE", "0.9")),
                "pitch": float(os.getenv("SATURDAY_TTS_PITCH", "0")),
                "volumeGainDb": 0
            }
        }
        
        try:
            logger.info(f" Enviando a Google TTS: {self.voice_name}")
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code != 200:
                logger.info(f" Error en Google TTS: {response.status_code}")
                logger.info(f"   {response.text[:200]}")
                return None
            
            data = response.json()
            audio_content = data.get("audioContent")
            if audio_content:
                logger.info(f" Audio generado ({len(audio_content)} caracteres base64)")
                return base64.b64decode(audio_content)
            else:
                logger.info(" No se recibi contenido de audio")
                return None
                
        except requests.exceptions.Timeout:
            logger.info(" Timeout en Google TTS")
            return None
        except Exception as e:
            logger.info(f" Error en Google TTS: {e}")
            return None
    
    def _play_audio(self, audio_data: bytes) -> bool:
        try:
            import threading
            import tempfile
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(audio_data)
                filename = tmp.name
            
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
                except OSError:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
            return True
        except Exception as e:
            logger.info(f" Error reproduciendo audio: {e}")
            return False
    
    # ============ STT (Speech-to-Text) con Google Cloud ============
    
    def convert_to_wav(self, input_path: str) -> Optional[str]:
        """Convierte cualquier audio a WAV (16kHz, mono, 16-bit)"""
        if not PYDUB_AVAILABLE:
            logger.info(" pydub no disponible, no se puede convertir")
            return None
        
        try:
            logger.info(f" Convirtiendo {input_path} a WAV...")
            
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
                logger.info(f" Convertido a: {output_path}")
                return output_path
                
        except Exception as e:
            logger.info(f" Error convirtiendo audio: {e}")
            return None

    def _build_stt_config(self, audio_path: str, converted_to_wav: bool, use_enhanced: bool = False) -> dict:
        """Arma el bloque 'config' de Google STT segn el formato real del archivo."""
        ext = os.path.splitext(audio_path)[1].lower()

        base_config = {
            "languageCode": self.language_code,
            "enableAutomaticPunctuation": True,
            # "command_and_search" est pensado para frases cortas de comando
            # (justo lo que dice un asistente de voz), a diferencia de
            # "latest_long" que es para audio largo tipo discurso/video.
            "model": "command_and_search",
            "audioChannelCount": 1,
            # Vocabulario esperado del asistente: ayuda a Google a inclinarse
            # hacia estas palabras cuando hay ambigedad.
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
        # en el proyecto de Google Cloud; si no est disponible, Google no
        # tira error, simplemente devuelve resultados vacos. Lo dejamos
        # apagado por defecto y solo se prueba explcitamente si se pide.
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
        y WAV/FLAC directamente. Solo convierte con pydub como ltimo recurso
        para formatos que Google no soporta de forma nativa.
        """
        if not self.api_key:
            logger.info(" No hay API key de Google")
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
                    logger.info(f" Formato '{ext}' no nativo, convirtiendo a WAV con pydub...")
                    audio = AudioSegment.from_file(audio_path)
                    audio = audio.set_frame_rate(16000)
                    audio = audio.set_channels(1)
                    audio = audio.set_sample_width(2)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                        wav_path = tmp_wav.name
                        audio.export(wav_path, format="wav")
                        logger.info(f" Convertido a WAV: {wav_path}")

                    audio_path_to_use = wav_path
                    converted_to_wav = True
                except Exception as e:
                    logger.info(f" Error en conversin (falta ffmpeg?): {e}")
                    logger.info("   Se intentar mandar el archivo original tal cual.")
                    audio_path_to_use = audio_path

            # 2. Leer el archivo de audio
            with open(audio_path_to_use, "rb") as f:
                audio_data = f.read()

            # 3. Codificar en base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            # DEBUG: tamao real del audio que se manda. Un archivo webm
            # de una frase hablada normal suele pesar varias decenas de KB;
            # si esto da muy pocos bytes (ej. <3-5 KB), es seal de que el
            # clip capturado es casi vaco aunque al reproducirlo "suene"
            # a algo (Opus comprime muchsimo el silencio/ruido de fondo).
            logger.info(f" Tamao del audio: {len(audio_data)} bytes ({len(audio_data)/1024:.1f} KB), "
                  f"base64: {len(audio_base64)} chars")

            # 4. Enviar a Google STT con la config correcta para el formato real.
            # Ya confirmamos que el sample rate (48000 para WEBM_OPUS del
            # navegador) NO es el problema: con la tasa correcta Google
            # responda 200 OK pero sin resultados. Ahora probamos variantes
            # de MODELO en vez de sample rate.
            url = "https://speech.googleapis.com/v1/speech:recognize"
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }

            # Variantes a probar en orden: primero el modelo pensado para
            # comandos cortos (lo normal para un asistente de voz), despus
            # sin modelo especfico (deja que Google elija el default), y
            # por ltimo con el modelo "enhanced" por si el proyecto s lo
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
                logger.info(f" Enviando a Google STT (model={attempt['model']}, useEnhanced={attempt['use_enhanced']})...")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                last_response = response

                if response.status_code != 200:
                    logger.info(f" Error en Google STT: {response.status_code}")
                    logger.info(f"   {response.text[:300]}")
                    continue

                data = response.json()
                if "results" in data and data["results"]:
                    transcript = data["results"][0].get("alternatives", [{}])[0].get("transcript", "")
                    logger.info(f" Reconocido con model={attempt['model']}: '{transcript}'")
                    return transcript.strip()

                logger.info(f"    200 OK pero sin resultados con model={attempt['model']}, probando otra variante...")

            # ltimo recurso: convertir a WAV con pydub/ffmpeg si no lo
            # habamos hecho ya (requiere ffmpeg Y ffprobe instalados).
            if not converted_to_wav and PYDUB_AVAILABLE:
                try:
                    logger.info(" Ninguna variante funcion con Opus, probando conversin a WAV como ltimo recurso...")
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
                            logger.info(f" Reconocido tras convertir a WAV: '{transcript}'")
                            return transcript.strip()
                    last_response = response
                except Exception as e:
                    logger.info(f" Fall tambin la conversin a WAV: {e}")

            if last_response is not None and last_response.status_code != 200:
                logger.info(f" Error final en Google STT: {last_response.status_code}")
                logger.info(f"   {last_response.text[:300]}")
            else:
                logger.info(" No se reconoci texto en ninguna variante probada (Google no detect habla)")
            return None

        except Exception as e:
            logger.info(f" Error en Google STT: {e}")
            return None
        finally:
            try:
                if wav_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
            except OSError:
                pass
    
    def listen_google(self, timeout: int = 5) -> Tuple[bool, str]:
        """Escucha y reconoce voz usando Google Cloud STT"""
        if not self.stt_available:
            logger.info(" STT no disponible")
            return False, ""
        
        logger.info(f" Escuchando (Google STT)...")
        
        try:
            import tempfile
            import wave
            
            # Grabar audio desde el micrfono
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
            logger.info(" Tiempo de espera agotado")
            return False, ""
        except Exception as e:
            logger.info(f" Error al escuchar: {e}")
            return False, ""
    
    def listen(self, timeout: int = 5) -> Tuple[bool, str]:
        """Escucha y reconoce voz usando el mtodo disponible"""
        # Intentar con Google STT
        if self.use_google and self.stt_available:
            try:
                return self.listen_google(timeout)
            except Exception as e:
                logger.info(f" Error en Google STT, usando fallback: {e}")
        
        # Fallback: speech_recognition local
        if self.stt_available:
            try:
                logger.info(f" Escuchando (fallback local)...")
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language_code)
                    logger.info(f" Escuch: '{text}'")
                    return True, text
                except sr.UnknownValueError:
                    logger.info(" No entend lo que dijiste")
                    return False, ""
                except sr.RequestError:
                    logger.info(" Error de conexin con el servicio de reconocimiento")
                    return False, ""
            except sr.WaitTimeoutError:
                logger.info(" Tiempo de espera agotado")
                return False, ""
            except Exception as e:
                logger.info(f" Error al escuchar: {e}")
                return False, ""
        
        logger.info(" No hay mtodo de reconocimiento de voz disponible")
        return False, ""

    def recognize_webm_file(self, audio_path: str) -> Optional[str]:
        """Mtodo legacy para compatibilidad"""
        return self.recognize_audio_file(audio_path)