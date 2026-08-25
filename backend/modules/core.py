# modules/core.py - Núcleo de Saturday COMPLETO
import os
import webbrowser
import re
from datetime import datetime
from typing import Dict, Any
import networkx as nx
import requests

# Importar módulos
try:
    from modules.notion_manager import NotionManager
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

try:
    from modules.data_manager import DataManager
    DATA_AVAILABLE = True
except ImportError:
    DATA_AVAILABLE = False

try:
    from modules.vault_manager import VaultManager
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

from modules.intent_engine import build_default_engine

try:
    from modules.voice import VoiceManager
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    from modules.calendar_manager import CalendarManager
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

try:
    from modules.email_manager import EmailManager
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

try:
    from modules.telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# IMPORTAR COMMUNICATION MANAGER (WhatsApp)
try:
    from backend.modules.communication import CommunicationManager
    COMMUNICATION_AVAILABLE = True
    print("✅ CommunicationManager importado correctamente")
except ImportError as e:
    COMMUNICATION_AVAILABLE = False
    print(f"⚠️ CommunicationManager no disponible: {e}")

try:
    from modules.daily_summary import DailySummary
    DAILY_SUMMARY_AVAILABLE = True
except ImportError:
    DAILY_SUMMARY_AVAILABLE = False
    print("⚠️ DailySummary no disponible")
    
try:
    from modules.scheduler import Scheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ Scheduler no disponible")
    
try:
    from modules.spotify_manager import SpotifyManager
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    print("⚠️ SpotifyManager no disponible")
    
try:
    from modules.news_manager import NewsManager
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("⚠️ NewsManager no disponible")
    
try:
    from modules.camera_manager import CameraManager
    CAMERA_AVAILABLE = True
    print("✅ CameraManager importado correctamente")
except ImportError as e:
    CAMERA_AVAILABLE = False
    print(f"⚠️ CameraManager no disponible: {e}")
    
class SaturdayCore:
    """Núcleo de inteligencia de Saturday"""
    
    def __init__(self):
        print("🧠 Inicializando núcleo de Saturday...")
        
        # Inicializar DataManager
        self.data = None
        if DATA_AVAILABLE:
            try:
                self.data = DataManager()
                print("✅ DataManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando DataManager: {e}")
        
        # Inicializar VaultManager (memoria en Markdown, "bóveda/")
        self.vault = None
        if VAULT_AVAILABLE:
            try:
                self.vault = VaultManager()
                print("✅ VaultManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando VaultManager: {e}")

        # Motor de interpretación de intenciones (sinónimos + fuzzy matching,
        # ver modules/intent_engine.py)
        self.intent_engine = build_default_engine()

        # Inicializar Notion
        self.notion = None
        if NOTION_AVAILABLE:
            try:
                api_key = os.getenv("NOTION_API_KEY")
                db_id = os.getenv("NOTION_DB_ID")
                if api_key and db_id:
                    self.notion = NotionManager(api_key, db_id)
                    print("✅ Notion conectado")
                else:
                    print("⚠️ NOTION_API_KEY o NOTION_DB_ID no configurados")
            except Exception as e:
                print(f"⚠️ Error conectando a Notion: {e}")
        
        # Inicializar VoiceManager
        self.voice = None
        if VOICE_AVAILABLE:
            try:
                self.voice = VoiceManager()
                print("✅ VoiceManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando VoiceManager: {e}")
        
        # Inicializar Calendar
        self.calendar = None
        if CALENDAR_AVAILABLE:
            try:
                self.calendar = CalendarManager()
                print("✅ CalendarManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando CalendarManager: {e}")
        
        # Inicializar Email
        self.email = None
        if EMAIL_AVAILABLE:
            try:
                self.email = EmailManager()
                print("✅ EmailManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando EmailManager: {e}")
        
        # Inicializar Telegram
        self.telegram = None
        if TELEGRAM_AVAILABLE:
            try:
                token = os.getenv("TELEGRAM_BOT_TOKEN")
                if token:
                    self.telegram = TelegramBot(self, token)
                    print("✅ TelegramBot inicializado")
                else:
                    print("⚠️ TELEGRAM_BOT_TOKEN no configurado")
            except Exception as e:
                print(f"⚠️ Error inicializando TelegramBot: {e}")
        
        # Inicializar Communication (WhatsApp)
        self.communication = None
        if COMMUNICATION_AVAILABLE:
            try:
                self.communication = CommunicationManager()
                print("✅ CommunicationManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando CommunicationManager: {e}")
                
        self.daily_summary = None
        if DAILY_SUMMARY_AVAILABLE:
            try:
                self.daily_summary = DailySummary(self)
                print("✅ DailySummary inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando DailySummary: {e}")
                
        self.scheduler = None
        if SCHEDULER_AVAILABLE:
            try:
                self.scheduler = Scheduler(self)
                print("✅ Scheduler inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando Scheduler: {e}")
        
        self.spotify = None
        if SPOTIFY_AVAILABLE:
            try:
                self.spotify = SpotifyManager()
                print("✅ SpotifyManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando SpotifyManager: {e}")
                
        self.news = None
        if NEWS_AVAILABLE:
            try:
                self.news = NewsManager()
                print("✅ NewsManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando NewsManager: {e}")
                
        # Inicializar Cámara
        self.camera = None
        if CAMERA_AVAILABLE:
            try:
                self.camera = CameraManager()
                print("✅ CameraManager inicializado")
            except Exception as e:
                print(f"⚠️ Error inicializando CameraManager: {e}")
        
        # Construir mapa de conocimiento
        self.knowledge_graph = nx.DiGraph()
        self.build_knowledge_graph()
        self.say_welcome()
        
        print("✅ Núcleo inicializado correctamente")
    
    def build_knowledge_graph(self):
        """Construye el mapa de nodos de conocimiento"""
        actions = {
            # Información
            "hora": self.get_time,
            "fecha": self.get_date,
            "clima": self.get_weather,
            
            # Tareas (Notion)
            "tareas": self.get_tasks,
            "buscar_tarea": self.search_task,
            "crear_tarea": self.create_task,
            "completar_tarea": self.complete_task,
            "eliminar_tarea": self.delete_task,
            "tareas_hoy": self.get_tasks_today,
            "tareas_completadas": self.get_completed_tasks,
            
            # Notas
            "crear_nota": self.create_note,
            "ver_notas": self.get_notes,
            "buscar_nota": self.search_notes,
            
            # Recordatorios
            "crear_recordatorio": self.create_reminder,
            "ver_recordatorios": self.get_reminders,
            "recordatorios_hoy": self.get_reminders_today,
            
            # Calendario
            "eventos": self.get_events,
            "eventos_hoy": self.get_events_today,
            "crear_evento": self.create_event,
            
            # Emails
            "correos": self.get_emails,
            "no_leidos": self.get_unread_emails,
            "enviar_correo": self.send_email,
            
            # Estadísticas
            "estadisticas": self.get_stats,
            
            # Comunicación (WhatsApp)
            "enviar_whatsapp": self.send_whatsapp,
            "enviar_voz_whatsapp": self.send_whatsapp_voice,
            
            # Otros
            "saludo": self.get_greeting,
            "ayuda": self.get_help,
            
            # Resumen diario
            "resumen_dia": self.send_daily_summary,
            
            # Spotify
            "abrir_spotify": self.open_spotify,
            "reproducir_musica": self.play_music,
            "pausar_musica": self.pause_music,
            "siguiente_cancion": self.next_track,
            "anterior_cancion": self.previous_track,
            "cancion_actual": self.current_track,
            
            # Noticias
            "noticias": self.get_news,
            "buscar_noticias": self.search_news,
            "noticias_resumen": self.get_news_summary,
            
            # Cámara
            "ver_cámara": self.get_camera,

            # Bóveda (memoria en Markdown)
            "guardar_boveda": self.guardar_en_boveda,
            "buscar_boveda": self.buscar_en_boveda,
            "estado_boveda": self.estado_boveda,
        }
        
        for name, func in actions.items():
            self.knowledge_graph.add_node(name, type="action", function=func)
        
        # Conexiones
        self.knowledge_graph.add_edge("saludo", "hora", weight=0.3)
        self.knowledge_graph.add_edge("saludo", "ayuda", weight=0.2)
        self.knowledge_graph.add_edge("hora", "fecha", weight=0.5)
        self.knowledge_graph.add_edge("tareas", "buscar_tarea", weight=0.3)
        self.knowledge_graph.add_edge("tareas", "tareas_hoy", weight=0.2)
        self.knowledge_graph.add_edge("tareas", "tareas_completadas", weight=0.1)
        self.knowledge_graph.add_edge("enviar_whatsapp", "enviar_voz_whatsapp", weight=0.5)
    
    def process_intent(self, text: str) -> Dict[str, Any]:
        """
        Procesa la intención del usuario.
        Usa IntentEngine (modules/intent_engine.py) para clasificar el texto
        contra sinónimos + fuzzy matching, en vez de comparar substrings a mano.
        """
        match = self.intent_engine.classify(text)

        if match is None:
            return {"intent": "general", "response": "No entendí tu petición. ¿Puedes repetirla?", "action": False}

        intent = match.intent
        params = dict(match.params)

        # ------------------------------------------------------------
        # Intención "abrir_noticias": no ejecuta nada en el backend, solo
        # le indica al frontend que cambie de vista (ver meta.navigate).
        # ------------------------------------------------------------
        if match.meta.get("navigate"):
            return {
                "intent": intent,
                "response": "Abriendo el panel de noticias 📰",
                "action": True,
                "navigate": match.meta["navigate"],
            }

        # ------------------------------------------------------------
        # Resto de intenciones: se ejecutan a través del knowledge_graph
        # (igual que antes, no se tocó esa parte).
        # ------------------------------------------------------------
        if intent in self.knowledge_graph:
            node = self.knowledge_graph.nodes[intent]
            if node.get('type') == 'action':
                try:
                    result = node['function'](**params)
                    self.send_to_telegram(f"📱 Interfaz: {text}")
                    self.send_to_telegram(f"🟣 Saturday: {result}")
                    return {"intent": intent, "response": result, "action": True}
                except Exception as e:
                    return {"intent": "error", "response": f"❌ Error: {str(e)}", "action": False}

        return {"intent": "general", "response": "No entendí tu petición. ¿Puedes repetirla?", "action": False}
    
    # ============ ACCIONES BÁSICAS ============
    
    def get_time(self, **kwargs) -> str:
        ahora = datetime.now()
        return f"Son las {ahora.strftime('%I:%M %p')}"
    
    def get_date(self, **kwargs) -> str:
        ahora = datetime.now()
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", 
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"Hoy es {dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year}"
    
    def get_weather(self, **kwargs) -> str:
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            if not api_key:
                return "❌ No configuraste la API del clima"
            city = os.getenv("SATURDAY_CITY", "Santiago")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return f"🌤️ El clima en {city} es {data['weather'][0]['description']} con {data['main']['temp']}°C"
            return "❌ Error obteniendo el clima"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_greeting(self, **kwargs) -> str:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos días"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        return f"{saludo}! Soy Saturday, tu asistente personal. ¿En qué puedo ayudarte?"
    
    def get_help(self, **kwargs) -> str:
        return """🟣 COMANDOS DE SATURDAY:

📋 TAREAS (Notion):
  • tareas - Tareas pendientes
  • crear tarea [nombre] - Crea una tarea
  • completar tarea [nombre] - Completa una tarea
  • eliminar tarea [nombre] - Elimina una tarea
  • tareas hoy - Tareas de hoy
  • tareas completadas - Tareas completadas

📝 NOTAS:
  • nota [texto] - Guarda una nota
  • ver notas - Muestra notas

⏰ RECORDATORIOS:
  • recordatorio [texto] a las [hora] - Crea recordatorio
  • ver recordatorios - Muestra recordatorios
  • recordatorios hoy - Recordatorios de hoy

📅 CALENDARIO:
  • eventos - Eventos próximos
  • eventos hoy - Eventos de hoy
  • crear evento [título] el [fecha] a las [hora]

📧 EMAILS:
  • correos - Correos recientes
  • no leídos - Correos no leídos
  • enviar correo a [email] asunto [asunto]

📱 WHATSAPP:
  • envía WhatsApp [mensaje] - Envía mensaje de texto
  • envía voz WhatsApp [mensaje] - Envía mensaje de voz

📊 ESTADÍSTICAS:
  • estadisticas - Estadísticas de uso

🕐 INFORMACIÓN:
  • hora - Hora actual
  • fecha - Fecha actual
  • clima - Clima
  
📰 NOTICIAS:
  • noticias - Noticias principales
  • noticias de [categoría] - Filtrar por categoría
  • buscar noticias [tema] - Buscar por tema
  • noticias resumen - Enviar resumen por WhatsApp

💬 OTROS:
  • hola - Saludo
  • ayuda - Esta ayuda"""
    
    # ============ TELEGRAM ============
    
    def send_to_telegram(self, text: str):
        """Envía un mensaje a Telegram si está disponible"""
        if self.telegram and hasattr(self.telegram, 'send_message'):
            try:
                self.telegram.send_message(text)
            except Exception as e:
                print(f"⚠️ Error enviando a Telegram: {e}")
    
    # ============ DELEGAR A MÓDULOS ============
    
    def get_tasks(self, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.get_tasks_formatted()
    
    def search_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.search_task(name)
    
    def create_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.create_task(name)
    
    def complete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.complete_task(name)
    
    def delete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.delete_task(name)
    
    def get_tasks_today(self, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.get_tasks_today()
    
    def get_completed_tasks(self, **kwargs) -> str:
        if not self.notion:
            return "❌ Notion no está configurado"
        return self.notion.get_completed_tasks()
    
    def create_note(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.create_note(text)
    
    def get_notes(self, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.get_notes()
    
    def search_notes(self, query: str = None, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.search_notes(query)
    
    def create_reminder(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.create_reminder(text)
    
    def get_reminders(self, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.get_reminders()
    
    def get_reminders_today(self, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.get_reminders_today()
    
    def get_stats(self, **kwargs) -> str:
        if not self.data:
            return "❌ DataManager no disponible"
        return self.data.get_stats()
    
    # ------------------------------------------------------------------
    # BÓVEDA (memoria en Markdown)
    # ------------------------------------------------------------------

    def guardar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Guarda algo dicho/capturado en raw/ de la bóveda."""
        if not self.vault:
            return "❌ VaultManager no disponible"
        if not text:
            return "¿Qué querés que guarde en la bóveda?"
        path = self.vault.save_raw(text, source="voz" if kwargs.get("voz") else "chat")
        return f"✅ Guardado en la bóveda: {path}"

    def buscar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Busca un texto en toda la bóveda."""
        if not self.vault:
            return "❌ VaultManager no disponible"
        if not text:
            return "¿Qué querés buscar en la bóveda?"
        results = self.vault.search(text)
        if not results:
            return f"No encontré nada con '{text}' en la bóveda."
        lines = [f"🔍 {len(results)} resultado(s) para '{text}':"]
        for r in results[:5]:
            lines.append(f"  📄 {r['path']}: ...{r['snippet']}...")
        return "\n".join(lines)

    def estado_boveda(self, **kwargs) -> str:
        """Resumen de la bóveda (cuántas notas hay en cada capa)."""
        if not self.vault:
            return "❌ VaultManager no disponible"
        return self.vault.get_stats_text()

    def get_camera(self, **kwargs) -> str:
        """Obtiene imagen/estado de la cámara"""
        if not self.camera:
            return "❌ CameraManager no disponible"
        return self.camera.get_status()
    
    def get_system_info(self, **kwargs) -> str:
        """Obtiene información del sistema (CPU, RAM, disco)"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f"💻 CPU: {cpu}% | 📟 RAM: {mem.percent}% ({mem.used//1024//1024}GB/{mem.total//1024//1024}GB) | "
                    f"💿 Disco: {disk.percent}% ({disk.used//1024//1024}GB/{disk.total//1024//1024}GB)")
        except ImportError:
            return "❌ psutil no está instalado en el backend"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_events(self, **kwargs) -> str:
        if not self.calendar:
            return "❌ CalendarManager no disponible"
        return self.calendar.get_events_formatted()
    
    def get_events_today(self, **kwargs) -> str:
        if not self.calendar:
            return "❌ CalendarManager no disponible"
        return self.calendar.get_events_today_formatted()
    
    def create_event(self, text: str = None, **kwargs) -> str:
        if not self.calendar:
            return "❌ CalendarManager no disponible"
        return self.calendar.create_event_from_text(text)
    
    def get_emails(self, **kwargs) -> str:
        if not self.email:
            return "❌ EmailManager no disponible"
        return self.email.get_emails_formatted()
    
    def get_unread_emails(self, **kwargs) -> str:
        if not self.email:
            return "❌ EmailManager no disponible"
        return self.email.get_unread_emails_formatted()
    
    def send_email(self, text: str = None, **kwargs) -> str:
        if not self.email:
            return "❌ EmailManager no disponible"
        return self.email.send_email_from_text(text)
    
    # ============ WHATSAPP (CommunicationManager) ============
    
    def send_whatsapp(self, text: str = None, **kwargs) -> str:
        """Envía un mensaje por WhatsApp"""
        if not self.communication:
            return "❌ CommunicationManager no disponible. Verifica la configuración."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "¿Qué mensaje quieres enviar? Dime: 'envía WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envía WhatsApp", "enviar WhatsApp", "envía wsp", "enviar wsp", "whatsapp"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendí el mensaje. Dime: 'envía WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_message(text)
        
        if result.get('success'):
            return f"📱 Mensaje enviado por WhatsApp: '{text}'"
        else:
            return f"❌ Error al enviar WhatsApp: {result.get('error')}"
    
    def send_whatsapp_voice(self, text: str = None, **kwargs) -> str:
        """Envía un mensaje de voz por WhatsApp"""
        if not self.communication:
            return "❌ CommunicationManager no disponible. Verifica la configuración."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "¿Qué mensaje de voz quieres enviar? Dime: 'envía voz WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envía voz WhatsApp", "enviar voz WhatsApp", "voz WhatsApp", "whatsapp voz"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendí el mensaje. Dime: 'envía voz WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_voice(text)
        
        if result.get('success'):
            return f"🎤 Mensaje de voz enviado por WhatsApp: '{text}'"
        else:
            return f"❌ Error al enviar voz WhatsApp: {result.get('error')}"
    
    def send_daily_summary(self, **kwargs) -> str:
        """Envía un resumen del día por WhatsApp"""
        if not self.daily_summary:
            return "❌ DailySummary no disponible"
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return "❌ WhatsApp no configurado. Verifica WHATSAPP_NUMBER y WHATSAPP_API_KEY"
        
        result = self.daily_summary.send(via="whatsapp")
        
        if result.get('success'):
            msg = "📋 Resumen del día enviado por WhatsApp. Revisa tu teléfono."
            if result.get('vault_path'):
                msg += f"\n🗂️ Guardado en la bóveda: {result['vault_path']}"
            return msg
        else:
            return f"❌ Error al enviar resumen: {result.get('error')}"
        
    def start_scheduler(self) -> str:
        """Inicia el planificador de tareas"""
        if not self.scheduler:
            return "❌ Scheduler no disponible"
        
        if self.scheduler.is_running:
            return "⏰ El scheduler ya está en ejecución"
        
        self.scheduler.start()
        return "⏰ Scheduler iniciado correctamente"

    def stop_scheduler(self) -> str:
        """Detiene el planificador de tareas"""
        if not self.scheduler:
            return "❌ Scheduler no disponible"
        
        if not self.scheduler.is_running:
            return "⏰ El scheduler ya está detenido"
        
        self.scheduler.stop()
        return "⏰ Scheduler detenido"

    def schedule_summary(self, hour: int = 8, minute: int = 0) -> str:
        """Programa el resumen diario"""
        if not self.scheduler:
            return "❌ Scheduler no disponible"
        
        self.scheduler.schedule_daily_summary(hour, minute)
        return f"📋 Resumen diario programado para las {hour:02d}:{minute:02d}"
    
    def open_spotify(self, **kwargs) -> str:
        """Abre Spotify Web"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        return self.spotify.open_spotify()

    def play_music(self, text: str = None, **kwargs) -> str:
        """Reproduce música en Spotify"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["reproduce", "reproducir", "pon", "toca", "play", "música", "canción", "cancion"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return self.spotify.play()
        
        return self.spotify.play(text)

    def pause_music(self, **kwargs) -> str:
        """Pausa la música"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        return self.spotify.pause()

    def next_track(self, **kwargs) -> str:
        """Siguiente canción"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        return self.spotify.next_track()

    def previous_track(self, **kwargs) -> str:
        """Canción anterior"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        return self.spotify.previous_track()

    def current_track(self, **kwargs) -> str:
        """Muestra la canción actual"""
        if not self.spotify:
            return "❌ Spotify no disponible"
        return self.spotify.get_current_track()
    
    def get_news(self, text: str = None, **kwargs) -> str:
        """Obtiene noticias principales"""
        if not self.news or not self.news.is_available():
            return "❌ Noticias no disponible. Verifica NEWS_API_KEY."
        
        # Detectar categoría
        category = None
        if text:
            categories = ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
            for cat in categories:
                if cat in text.lower():
                    category = cat
                    break
        
        articles = self.news.get_top_headlines(category=category, limit=7)
        return self.news.format_news(articles)

    def search_news(self, text: str = None, **kwargs) -> str:
        """Busca noticias por tema"""
        if not self.news or not self.news.is_available():
            return "❌ Noticias no disponible. Verifica NEWS_API_KEY."
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["buscar noticias", "buscar noticia", "noticias de", "noticias sobre", "buscar"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return "¿Qué tema quieres buscar? Dime: 'buscar noticias [tema]'"
        
        articles = self.news.search_news(text, limit=5)
        return self.news.format_news(articles)

    def get_news_summary(self, **kwargs) -> str:
        """Envía un resumen de noticias por WhatsApp"""
        if not self.news or not self.news.is_available():
            return "❌ Noticias no disponible. Verifica NEWS_API_KEY."
        
        articles = self.news.get_top_headlines(limit=5)
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return self.news.format_news(articles)
        
        # Enviar por WhatsApp
        message = self.news.format_news_for_whatsapp(articles)
        result = self.communication.send_whatsapp_message(message)
        
        if result.get('success'):
            return "📰 Resumen de noticias enviado por WhatsApp"
        else:
            return self.news.format_news(articles)
        
    def say_welcome(self):
        """Saluda con voz al iniciar el sistema"""
        try:
            import time
            # Esperar 1 segundo para que todo esté listo
            time.sleep(1)
            
            hora = datetime.now().hour
            if hora < 12:
                saludo = "Buenos días"
            elif hora < 19:
                saludo = "Buenas tardes"
            else:
                saludo = "Buenas noches"
            
            mensaje = f"{saludo}! Soy Saturday, tu asistente personal. Estoy listo para ayudarte."
            
            # Hablar con Google TTS
            if self.voice:
                self.voice.speak(mensaje)
                print(f"🗣️ Saturday: {mensaje}")
            else:
                print(f"📝 Saturday: {mensaje}")
                
        except Exception as e:
            print(f"⚠️ Error en saludo de voz: {e}")