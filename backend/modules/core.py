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
        
        # Construir mapa de conocimiento
        self.knowledge_graph = nx.DiGraph()
        self.build_knowledge_graph()
        
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
        """Procesa la intención del usuario"""
        text_lower = text.lower()
        intent = "general"
        params = {}
        
        # ============================================================
        # DETECTAR COMANDOS DE WHATSAPP (prioridad alta)
        # ============================================================
        if "envía whatsapp" in text_lower or "enviar whatsapp" in text_lower or "envía wsp" in text_lower:
            intent = "enviar_whatsapp"
            params["text"] = text
            print(f"📱 Detectado comando WhatsApp: {text}")
            # Ejecutar directamente
            node = self.knowledge_graph.nodes[intent]
            if node.get('type') == 'action':
                try:
                    result = node['function'](**params)
                    self.send_to_telegram(f"📱 Interfaz: {text}")
                    self.send_to_telegram(f"🟣 Saturday: {result}")
                    return {"intent": intent, "response": result, "action": True}
                except Exception as e:
                    return {"intent": "error", "response": f"❌ Error: {str(e)}", "action": False}
        
        if "envía voz whatsapp" in text_lower or "enviar voz whatsapp" in text_lower or "voz whatsapp" in text_lower:
            intent = "enviar_voz_whatsapp"
            params["text"] = text
            print(f"🎤 Detectado comando WhatsApp voz: {text}")
            node = self.knowledge_graph.nodes[intent]
            if node.get('type') == 'action':
                try:
                    result = node['function'](**params)
                    self.send_to_telegram(f"📱 Interfaz: {text}")
                    self.send_to_telegram(f"🟣 Saturday: {result}")
                    return {"intent": intent, "response": result, "action": True}
                except Exception as e:
                    return {"intent": "error", "response": f"❌ Error: {str(e)}", "action": False}
        
        # ============================================================
        # MAPEO DE INTENCIONES (resto de comandos)
        # ============================================================
        intent_map = [
            # ============================================================
            # SPOTIFY (prioridad alta)
            # ============================================================
            ("abrir spotify", "abrir_spotify"),
            ("abre spotify", "abrir_spotify"),
            ("reproduce", "reproducir_musica"),
            ("reproducir", "reproducir_musica"),
            ("pon música", "reproducir_musica"),
            ("pon musica", "reproducir_musica"),
            ("toca", "reproducir_musica"),
            ("toca música", "reproducir_musica"),
            ("play", "reproducir_musica"),
            ("pausa", "pausar_musica"),
            ("pausar", "pausar_musica"),
            ("siguiente", "siguiente_cancion"),
            ("siguiente canción", "siguiente_cancion"),
            ("siguiente tema", "siguiente_cancion"),
            ("anterior", "anterior_cancion"),
            ("canción actual", "cancion_actual"),
            ("qué suena", "cancion_actual"),
            ("qué música suena", "cancion_actual"),
            ("que suena", "cancion_actual"),
            
            # ============================================================
            # TAREAS
            # ============================================================
            ("buscar tarea", "buscar_tarea"),
            ("crear tarea", "crear_tarea"),
            ("completar tarea", "completar_tarea"),
            ("eliminar tarea", "eliminar_tarea"),
            ("tareas hoy", "tareas_hoy"),
            ("tareas completadas", "tareas_completadas"),
            ("tareas", "tareas"),
            
            # ============================================================
            # NOTAS
            # ============================================================
            ("nota", "crear_nota"),
            ("ver notas", "ver_notas"),
            ("buscar nota", "buscar_nota"),
            
            # ============================================================
            # RECORDATORIOS
            # ============================================================
            ("recordatorio", "crear_recordatorio"),
            ("ver recordatorios", "ver_recordatorios"),
            ("recordatorios hoy", "recordatorios_hoy"),
            
            # ============================================================
            # CALENDARIO
            # ============================================================
            ("eventos", "eventos"),
            ("eventos hoy", "eventos_hoy"),
            ("crear evento", "crear_evento"),
            
            # ============================================================
            # EMAILS
            # ============================================================
            ("correos", "correos"),
            ("no leídos", "no_leidos"),
            ("enviar correo", "enviar_correo"),
            
            # ============================================================
            # INFORMACIÓN
            # ============================================================
            ("hora", "hora"),
            ("fecha", "fecha"),
            ("clima", "clima"),
            ("temperatura", "clima"),
            
            # ============================================================
            # ESTADÍSTICAS
            # ============================================================
            ("estadisticas", "estadisticas"),
            
            # ============================================================
            # OTROS
            # ============================================================
            ("hola", "saludo"),
            ("ayuda", "ayuda"),
        ]
        
        for key, value in intent_map:
            if key in text_lower:
                intent = value
                # Extraer parámetros
                if intent in ["crear_tarea", "completar_tarea", "eliminar_tarea", "buscar_tarea"]:
                    params["name"] = text.replace(key, "").strip()
                elif intent in ["crear_nota", "crear_recordatorio", "crear_evento", "enviar_correo"]:
                    params["text"] = text.replace(key, "").strip()
                break
        
        # Ejecutar acción
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
            return "📋 Resumen del día enviado por WhatsApp. Revisa tu teléfono."
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