# modules/core.py - Núcleo de Saturday CORREGIDO
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

# ✅ IMPORTAR TELEGRAM
try:
    from modules.telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


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
        
        # ✅ INICIALIZAR TELEGRAM
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
        
        # Construir mapa de conocimiento
        self.knowledge_graph = nx.DiGraph()
        self.build_knowledge_graph()
        
        print("✅ Núcleo inicializado correctamente")
    
    def build_knowledge_graph(self):
        """Construye el mapa de nodos de conocimiento"""
        actions = {
            "hora": self.get_time,
            "fecha": self.get_date,
            "clima": self.get_weather,
            "tareas": self.get_tasks,
            "buscar_tarea": self.search_task,
            "crear_tarea": self.create_task,
            "completar_tarea": self.complete_task,
            "eliminar_tarea": self.delete_task,
            "tareas_hoy": self.get_tasks_today,
            "tareas_completadas": self.get_completed_tasks,
            "crear_nota": self.create_note,
            "ver_notas": self.get_notes,
            "buscar_nota": self.search_notes,
            "crear_recordatorio": self.create_reminder,
            "ver_recordatorios": self.get_reminders,
            "recordatorios_hoy": self.get_reminders_today,
            "eventos": self.get_events,
            "eventos_hoy": self.get_events_today,
            "crear_evento": self.create_event,
            "correos": self.get_emails,
            "no_leidos": self.get_unread_emails,
            "enviar_correo": self.send_email,
            "estadisticas": self.get_stats,
            "saludo": self.get_greeting,
            "ayuda": self.get_help,
        }
        
        for name, func in actions.items():
            self.knowledge_graph.add_node(name, type="action", function=func)
    
    def process_intent(self, text: str) -> Dict[str, Any]:
        """Procesa la intención del usuario"""
        text_lower = text.lower()
        intent = "general"
        params = {}
        
        # Mapeo simple de intenciones
        intent_map = [
            ("hora", "hora"),
            ("fecha", "fecha"),
            ("clima", "clima"),
            ("temperatura", "clima"),
            ("tareas", "tareas"),
            ("buscar tarea", "buscar_tarea"),
            ("crear tarea", "crear_tarea"),
            ("completar tarea", "completar_tarea"),
            ("eliminar tarea", "eliminar_tarea"),
            ("tareas hoy", "tareas_hoy"),
            ("tareas completadas", "tareas_completadas"),
            ("nota", "crear_nota"),
            ("ver notas", "ver_notas"),
            ("buscar nota", "buscar_nota"),
            ("recordatorio", "crear_recordatorio"),
            ("ver recordatorios", "ver_recordatorios"),
            ("recordatorios hoy", "recordatorios_hoy"),
            ("eventos", "eventos"),
            ("eventos hoy", "eventos_hoy"),
            ("crear evento", "crear_evento"),
            ("correos", "correos"),
            ("no leídos", "no_leidos"),
            ("enviar correo", "enviar_correo"),
            ("estadisticas", "estadisticas"),
            ("hola", "saludo"),
            ("ayuda", "ayuda"),
        ]
        
        for key, value in intent_map:
            if key in text_lower:
                intent = value
                # Extraer parámetros
                if intent in ["crear_tarea", "completar_tarea", "eliminar_tarea", "buscar_tarea"]:
                    params["name"] = text.replace(key, "").strip()
                elif intent in ["crear_nota"]:
                    params["text"] = text.replace(key, "").strip()
                elif intent in ["crear_recordatorio"]:
                    params["text"] = text.replace(key, "").strip()
                elif intent in ["crear_evento"]:
                    params["text"] = text.replace(key, "").strip()
                elif intent in ["enviar_correo"]:
                    params["text"] = text.replace(key, "").strip()
                break
        
        # Ejecutar acción
        if intent in self.knowledge_graph:
            node = self.knowledge_graph.nodes[intent]
            if node.get('type') == 'action':
                try:
                    result = node['function'](**params)
                    
                    # ✅ ENVIAR A TELEGRAM SI ESTÁ DISPONIBLE
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

📋 TAREAS:
  • tareas - Tareas pendientes
  • crear tarea [nombre] - Crea una tarea
  • completar tarea [nombre] - Completa una tarea
  • eliminar tarea [nombre] - Elimina una tarea

📝 NOTAS:
  • nota [texto] - Guarda una nota
  • ver notas - Muestra notas

⏰ RECORDATORIOS:
  • recordatorio [texto] a las [hora] - Crea recordatorio
  • ver recordatorios - Muestra recordatorios

📅 CALENDARIO:
  • eventos - Eventos próximos
  • eventos hoy - Eventos de hoy
  • crear evento [título] el [fecha] a las [hora]

📧 EMAILS:
  • correos - Correos recientes
  • no leídos - Correos no leídos
  • enviar correo a [email] asunto [asunto]

🕐 INFORMACIÓN:
  • hora - Hora actual
  • fecha - Fecha actual
  • clima - Clima

📊 ESTADÍSTICAS:
  • estadisticas - Estadísticas de uso

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