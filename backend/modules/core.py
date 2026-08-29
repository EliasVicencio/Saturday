# modules/core.py - Nucleo de Saturday COMPLETO
import os
from datetime import datetime
from typing import Dict, Any
import networkx as nx
from modules.http_utils import get_with_retry
from modules.config import config

# Importar modulos
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

# IMPORTAR ZAPIER WEBHOOK
try:
    from modules.make_webhook import MakeWebhook
    MAKE_AVAILABLE = True
except ImportError:
    MAKE_AVAILABLE = False

try:
    from modules.telegram_bot import TelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# IMPORTAR COMMUNICATION MANAGER (WhatsApp)
try:
    from modules.communication import CommunicationManager
    COMMUNICATION_AVAILABLE = True
    print(" CommunicationManager importado correctamente")
except ImportError as e:
    COMMUNICATION_AVAILABLE = False
    print(f" CommunicationManager no disponible: {e}")

try:
    from modules.daily_summary import DailySummary
    DAILY_SUMMARY_AVAILABLE = True
except ImportError:
    DAILY_SUMMARY_AVAILABLE = False
    print(" DailySummary no disponible")
    
try:
    from modules.scheduler import Scheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print(" Scheduler no disponible")
    
try:
    from modules.spotify_manager import SpotifyManager
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    print(" SpotifyManager no disponible")
    
try:
    from modules.news_manager import NewsManager
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print(" NewsManager no disponible")
    
try:
    from modules.camera_manager import CameraManager
    CAMERA_AVAILABLE = True
    print(" CameraManager importado correctamente")
except ImportError as e:
    CAMERA_AVAILABLE = False
    print(f" CameraManager no disponible: {e}")

try:
    from modules.conversation_manager import ConversationManager
    CONVERSATION_AVAILABLE = True
except ImportError:
    CONVERSATION_AVAILABLE = False

try:
    from modules.gemini_chat import GeminiChat
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from modules.memory.store import MemoryStore
    from modules.memory.retrieval import MemoryRetriever
    from modules.memory.summarizer import MemorySummarizer
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from modules.events.bus import EventBus
    EVENTS_AVAILABLE = True
except ImportError:
    EVENTS_AVAILABLE = False

try:
    from modules.security.privacy import PrivacyManager
    PRIVACY_AVAILABLE = True
except ImportError:
    PRIVACY_AVAILABLE = False

try:
    from modules.vision.describer import VisionDescriber
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

try:
    from modules.agents.router import AgentRouter
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False

try:
    from modules.tools.registry import ToolRegistry
    from modules.tools.builtin import register_all as register_builtin_tools
    TOOLREG_AVAILABLE = True
except ImportError:
    TOOLREG_AVAILABLE = False

try:
    from modules.security.audit import AuditLogger
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

try:
    from modules.security.permissions import PermissionManager
    PERMS_AVAILABLE = True
except ImportError:
    PERMS_AVAILABLE = False

class SaturdayCore:
    """Nucleo de inteligencia de Saturday"""

    def _execute_tool(self, tool_name, tool_args):
        """Execute a tool by name with arguments. Returns string result."""
        try:
            if tool_name == "get_weather":
                city = tool_args.get("city", config.saturday_city)
                return self.get_weather()
            elif tool_name == "get_time":
                return self.get_time()
            elif tool_name == "get_tasks":
                return self.get_tasks()
            elif tool_name == "create_task":
                return self.create_task(tool_args.get("name", ""))
            elif tool_name == "get_news":
                return self.get_news()
            elif tool_name == "get_events":
                return self.get_events()
            elif tool_name == "search_vault":
                return self.search_notes(tool_args.get("query", ""))
            elif tool_name == "describe_scene":
                return self._describe_scene(tool_args.get("question", "Que hay en la imagen?"))
            elif tool_name == "privacy_status":
                return self._privacy_status()
            else:
                return f"Tool desconocida: {tool_name}"
        except Exception as e:
            return f"Error ejecutando {tool_name}: {str(e)}"
    
    def __init__(self):
        print(" Inicializando nucleo de Saturday...")
        
        # Inicializar DataManager
        self.data = None
        if DATA_AVAILABLE:
            try:
                self.data = DataManager()
                print(" DataManager inicializado")
            except Exception as e:
                print(f" Error inicializando DataManager: {e}")
        
        # Inicializar VaultManager (memoria en Markdown, "boveda/")
        self.vault = None
        if VAULT_AVAILABLE:
            try:
                self.vault = VaultManager()
                print(" VaultManager inicializado")
            except Exception as e:
                print(f" Error inicializando VaultManager: {e}")

        # Motor de interpretacion de intenciones (sinonimos + fuzzy matching,
        # ver modules/intent_engine.py)
        self.intent_engine = build_default_engine()

        # Inicializar Notion
        self.notion = None
        if NOTION_AVAILABLE:
            try:
                if config.notion_api_key and config.notion_db_id:
                    self.notion = NotionManager(config.notion_api_key, config.notion_db_id)
                    print(" Notion conectado")
                else:
                    print("  NOTION_API_KEY o NOTION_DB_ID no configurados")
            except Exception as e:
                print(f"  Error conectando a Notion: {e}")
        
        # Inicializar VoiceManager
        self.voice = None
        if VOICE_AVAILABLE:
            try:
                self.voice = VoiceManager()
                print(" VoiceManager inicializado")
            except Exception as e:
                print(f" Error inicializando VoiceManager: {e}")
        
        # Inicializar Calendar
        self.calendar = None
        if CALENDAR_AVAILABLE:
            try:
                self.calendar = CalendarManager()
                print(" CalendarManager inicializado")
            except Exception as e:
                print(f" Error inicializando CalendarManager: {e}")
        
        # Inicializar Zapier Webhooks
        self.make = None
        if MAKE_AVAILABLE:
            try:
                self.make = MakeWebhook()
                print(" MakeWebhook inicializado")
            except Exception as e:
                print(f" Error inicializando MakeWebhook: {e}")
        
        # Inicializar Email
        self.email = None
        if EMAIL_AVAILABLE:
            try:
                self.email = EmailManager()
                print(" EmailManager inicializado")
            except Exception as e:
                print(f" Error inicializando EmailManager: {e}")
        
        # Inicializar Telegram
        self.telegram = None
        if TELEGRAM_AVAILABLE:
            try:
                if config.telegram_bot_token:
                    self.telegram = TelegramBot(self, config.telegram_bot_token)
                    print(" TelegramBot inicializado")
                else:
                    print("  TELEGRAM_BOT_TOKEN no configurado")
            except Exception as e:
                print(f"  Error inicializando TelegramBot: {e}")
        
        # Inicializar Communication (WhatsApp)
        self.communication = None
        if COMMUNICATION_AVAILABLE:
            try:
                self.communication = CommunicationManager()
                print(" CommunicationManager inicializado")
            except Exception as e:
                print(f" Error inicializando CommunicationManager: {e}")
                
        self.daily_summary = None
        if DAILY_SUMMARY_AVAILABLE:
            try:
                self.daily_summary = DailySummary(self)
                print(" DailySummary inicializado")
            except Exception as e:
                print(f" Error inicializando DailySummary: {e}")
                
        self.scheduler = None
        if SCHEDULER_AVAILABLE:
            try:
                self.scheduler = Scheduler(self)
                print(" Scheduler inicializado")
            except Exception as e:
                print(f" Error inicializando Scheduler: {e}")
        
        self.spotify = None
        if SPOTIFY_AVAILABLE:
            try:
                self.spotify = SpotifyManager()
                print(" SpotifyManager inicializado")
            except Exception as e:
                print(f" Error inicializando SpotifyManager: {e}")
                
        self.news = None
        if NEWS_AVAILABLE:
            try:
                self.news = NewsManager()
                print(" NewsManager inicializado")
            except Exception as e:
                print(f" Error inicializando NewsManager: {e}")
                
        # Inicializar Camara
        self.camera = None
        if CAMERA_AVAILABLE:
            try:
                self.camera = CameraManager()
                print(" CameraManager inicializado")
            except Exception as e:
                print(f" Error inicializando CameraManager: {e}")
        
        # Inicializar ConversationManager (memoria conversacional)
        self.conversation = None
        if CONVERSATION_AVAILABLE:
            try:
                self.conversation = ConversationManager()
                print(" ConversationManager inicializado")
            except Exception as e:
                print(f" Error inicializando ConversationManager: {e}")
        
        # Inicializar memoria persistente (SQLite)
        self.memory_store = None
        self.memory_retriever = None
        self.memory_summarizer = None
        if MEMORY_AVAILABLE:
            try:
                self.memory_store = MemoryStore()
                self.memory_retriever = MemoryRetriever(self.memory_store)
                self.memory_summarizer = MemorySummarizer(self.memory_store)
                print("[OK] MemoryStore inicializado (SQLite)")
            except Exception as e:
                print(f"[WARN] Error inicializando MemoryStore: {e}")

        # Inicializar GeminiChat (LLM conversacional)
        self.gemini = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini = GeminiChat()
                print("[OK] GeminiChat inicializado")
            except Exception as e:
                print(f"[WARN] Error inicializando GeminiChat: {e}")

        # Inicializar Event Bus
        self.event_bus = None
        if EVENTS_AVAILABLE:
            try:
                self.event_bus = EventBus()
                print("[OK] EventBus inicializado")
            except Exception as e:
                print(f"[WARN] Error inicializando EventBus: {e}")

        # Inicializar Privacy Manager
        self.privacy = None
        if PRIVACY_AVAILABLE:
            try:
                self.privacy = PrivacyManager()
                print("[OK] PrivacyManager inicializado")
            except Exception as e:
                print(f"[WARN] Error inicializando PrivacyManager: {e}")

        # Inicializar Vision Describer
        self.vision = None
        if VISION_AVAILABLE:
            try:
                self.vision = VisionDescriber()
            except Exception as e:
                print(f"[WARN] Error inicializando VisionDescriber: {e}")

        # Inicializar Agent Router (Level 5)
        self.agent_router = None
        if AGENTS_AVAILABLE:
            try:
                self.agent_router = AgentRouter(core=self)
                print("[OK] AgentRouter inicializado (Level 5)")
            except Exception as e:
                print(f"[WARN] Error inicializando AgentRouter: {e}")

        # Inicializar Tool Registry
        self.tool_registry = None
        if TOOLREG_AVAILABLE:
            try:
                self.tool_registry = ToolRegistry()
                register_builtin_tools(self.tool_registry)
                print(f"[OK] ToolRegistry inicializado ({len(self.tool_registry.list_tools())} tools)")
            except Exception as e:
                print(f"[WARN] Error inicializando ToolRegistry: {e}")

        # Inicializar Audit Logger
        self.audit = None
        if AUDIT_AVAILABLE:
            try:
                self.audit = AuditLogger()
                print("[OK] AuditLogger inicializado")
            except Exception as e:
                print(f"[WARN] Error inicializando AuditLogger: {e}")

        # Inicializar Permission Manager
        self.permissions = None
        if PERMS_AVAILABLE:
            try:
                self.permissions = PermissionManager()
                print("[OK] PermissionManager inicializado")
            except Exception as e:
                print(f"[WARN] Error inicializando PermissionManager: {e}")

        # Construir mapa de conocimiento
        self.knowledge_graph = nx.DiGraph()
        self.build_knowledge_graph()
        
        # Auto-iniciar scheduler y programar tareas autonomas
        self._setup_autonomous_tasks()
        
        print(" Nucleo inicializado correctamente")
    
    def _describe_scene(self, question: str = "Que hay en la imagen?") -> str:
        if not self.privacy or not self.privacy.is_enabled("camera_enabled"):
            return "La camara esta desactivada por privacidad"
        if not self.camera:
            return "Camara no disponible"
        img_b64 = self.camera.capture()
        if not img_b64:
            return "No se pudo capturar imagen"
        if self.vision and self.vision.is_available:
            import tempfile, base64
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(base64.b64decode(img_b64))
                tmp_path = f.name
            try:
                desc = self.vision.describe(tmp_path, question)
                return desc or "No pude describir la imagen"
            finally:
                os.unlink(tmp_path)
        return "Vision no disponible (requiere GROQ_API_KEY)"

    def _privacy_status(self) -> str:
        if not self.privacy:
            return "PrivacyManager no disponible"
        state = self.privacy.get_state()
        lines = ["ESTADO DE PRIVACIDAD:"]
        for k, v in state.items():
            icon = "ON" if v else "OFF"
            lines.append(f"  {icon} {k}")
        return "\n".join(lines)

    def build_knowledge_graph(self):
        """Construye el mapa de nodos de conocimiento"""
        actions = {
            # Informacion
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
            
            # Estadisticas
            "estadisticas": self.get_stats,
            "system_info": self.get_system_info,
            
            # Comunicacion (WhatsApp)
            "enviar_whatsapp": self.send_whatsapp,
            "enviar_voz_whatsapp": self.send_whatsapp_voice,
            
            # Otros
            "saludo": self.get_greeting,
            "ayuda": self.get_help,
            
            # Resumen diario
            "resumen_dia": self.send_daily_summary,
            
            # Status
            "status": self.get_status,
            
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
            
            # Camara
            "get_camera": self.get_camera,

            # Boveda (memoria en Markdown)
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
    
    def process_intent(self, text: str, chat_id: int = None) -> Dict[str, Any]:
        """
        Procesa la intencion del usuario con contexto conversacional.
        Si chat_id se provee, usa memoria de conversacion.
        """
        # Registrar mensaje del usuario si hay contexto
        if chat_id and self.conversation:
            ctx = self.conversation.get_context(chat_id)
            
            # Detectar preguntas de seguimiento
            if self.conversation.is_followup(text) and ctx.last_topic:
                return self._handle_followup(chat_id, text, ctx)
            
            self.conversation.add_user_message(chat_id, text)
        
        match = self.intent_engine.classify(text)

        if match is None:
            # === GEMINI FALLBACK: respuesta conversacional ===
            if self.gemini:
                try:
                    # Inyectar contexto de memoria antes de responder
                    memory_context = ""
                    if self.memory_retriever:
                        memory_context = self.memory_retriever.before_respond(text, chat_id)

                    # Combinar contexto historial + memoria
                    full_context = text
                    if memory_context:
                        full_context = memory_context + "\n\nMensaje del usuario: " + text

                    # Extraer y guardar recuerdos del usuario
                    if self.memory_summarizer:
                        self.memory_summarizer.process_and_save(text, chat_id)

                    gemini_response = self.gemini.chat(full_context, chat_id=chat_id)
                    if gemini_response:
                        response = gemini_response
                    else:
                        response = "No pude procesar tu mensaje. Intenta de nuevo."
                except Exception as e:
                    response = "Hubo un error procesando tu mensaje. Intenta de nuevo."
            else:
                response = "No entendí tu petición. Puedes repetirla o decir 'ayuda' para ver qué puedo hacer?"
            
            if chat_id and self.conversation:
                self.conversation.add_assistant_message(chat_id, response, "general")
            
            return {"intent": "general", "response": response, "action": False}

        intent = match.intent
        params = dict(match.params)

        # Registrar en contexto
        if chat_id and self.conversation:
            ctx = self.conversation.get_context(chat_id)
            ctx.last_topic = intent
            self.conversation.clear_pending_question(chat_id)

        # ------------------------------------------------------------
        # Intencion "abrir_noticias": solo indica al frontend cambiar vista
        # ------------------------------------------------------------
        if match.meta.get("navigate"):
            response = "Abriendo el panel de noticias o"
            if chat_id and self.conversation:
                self.conversation.add_assistant_message(chat_id, response, intent)
            return {
                "intent": intent,
                "response": response,
                "action": True,
                "navigate": match.meta["navigate"],
            }

        # ------------------------------------------------------------
        # Resto de intenciones: se ejecutan a traves del knowledge_graph
        # ------------------------------------------------------------
        if intent in self.knowledge_graph:
            node = self.knowledge_graph.nodes[intent]
            if node.get('type') == 'action':
                try:
                    result = node['function'](**params)
                    
                    # Agregar contexto natural a la respuesta
                    if chat_id and self.conversation:
                        result = self._enrich_response(intent, result, chat_id)
                        self.conversation.add_assistant_message(chat_id, result, intent)
                    
                    self.send_to_telegram(f" Interfaz: {text}")
                    self.send_to_telegram(f" Saturday: {result}")
                    return {"intent": intent, "response": result, "action": True}
                except Exception as e:
                    return {"intent": "error", "response": f" Error: {str(e)}", "action": False}

        return {"intent": "general", "response": "No entendi tu peticion. ?Puedes repetirla?", "action": False}

    def process_via_router(self, text: str, chat_id: int = None, session_id: str = "") -> Dict[str, Any]:
        """
        Procesa usando el AgentRouter (Level 5).
        Retorna resultado estructurado con info de routing.
        """
        if self.agent_router:
            return self.agent_router.route(text, chat_id=chat_id, session_id=session_id)
        # Fallback al metodo legacy
        return self.process_intent(text, chat_id=chat_id)
    
    def _enrich_response(self, intent: str, result: str, chat_id: int) -> str:
        """
        Enriquece la respuesta con contexto conversacional.
        Agrega follow-ups naturales segun la intencion.
        """
        if not self.conversation:
            return result
        
        ctx = self.conversation.get_context(chat_id)
        
        # Follow-ups naturales segun intencion
        followups = {
            "clima": " ?Te parece si te aviso si cambia el clima?",
            "hora": " ?Necesitas que te recuerde algo para despues?",
            "fecha": " ?Tienes algun evento hoy?",
            "tareas": " ?Quieres que te ayude con alguna?",
            "noticias": " ?Te interesa algun tema en particular?",
            "correos": " ?Quieres que responda alguno?",
        }
        
        if intent in followups and len(result) < 200:
            result += followups[intent]
            self.conversation.set_pending_question(chat_id, followups[intent].strip())
        
        return result
    
    def _handle_followup(self, chat_id: int, text: str, ctx) -> Dict[str, Any]:
        """Maneja preguntas de seguimiento basadas en el contexto"""
        last_topic = ctx.last_topic
        
        # Mapear topic a acciones de seguimiento
        followup_responses = {
            "clima": "El clima es algo que cambia seguido. ?Quieres que te avise si hay lluvia pronosticada?",
            "hora": "La hora no cambia mucho. ?Necesitas programar algo?",
            "fecha": self._fecha_es(),
            "tareas": "?Quieres que te muestre las tareas pendientes o creemos una nueva?",
            "noticias": "?Hay algun tema que te interese mas? Puedo buscar noticias especificas.",
            "correos": "?Quieres que revise tus correos no leidos?",
            "spotify": "?Quieres que ponga algo de musica?",
        }
        
        response = followup_responses.get(last_topic, 
            f"Estabamos hablando de {last_topic}. ?Que quieres saber?")
        
        self.conversation.add_assistant_message(chat_id, response, "followup")
        
        return {"intent": "followup", "response": response, "action": False}
    
    # ============ ACCIONES BÁSICAS ============
    
    def get_status(self, **kwargs) -> str:
        """Estado general de Saturday"""
        modules = []
        
        # Verificar modulos
        if self.notion:
            modules.append(" Notion")
        else:
            modules.append(" Notion")
        
        if self.calendar:
            modules.append(" Calendario")
        else:
            modules.append(" Calendario")
        
        if self.email:
            modules.append(" Correos")
        else:
            modules.append(" Correos")
        
        if self.communication:
            modules.append(" WhatsApp")
        else:
            modules.append(" WhatsApp")
        
        if self.news:
            modules.append(" Noticias")
        else:
            modules.append(" Noticias")
        
        if self.voice:
            modules.append(" Voz (TTS/STT)")
        else:
            modules.append(" Voz")
        
        if self.scheduler:
            scheduler_status = " Activo" if self.scheduler.is_running else " Detenido"
            modules.append(f" Scheduler: {scheduler_status}")
        
        if self.conversation:
            modules.append(" Memoria conversacional")
        else:
            modules.append(" Memoria conversacional")
        
        # Informacion del sistema
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            sys_info = f" CPU: {cpu}% | RAM: {mem.percent}%"
        except (ImportError, Exception):
            sys_info = ""
        
        response = "**ESTADO DE SATURDAY**\n\n"
        response += "\n".join(modules)
        if sys_info:
            response += f"\n\n{sys_info}"
        
        return response
    
    def get_time(self, **kwargs) -> str:
        ahora = datetime.now()
        return f"Son las {ahora.strftime('%H:%M')}"
    
    def get_date(self, **kwargs) -> str:
        ahora = datetime.now()
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", 
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"Hoy es {dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year}"
    
    def _setup_autonomous_tasks(self):
        """Configura tareas autonomas del scheduler"""
        if not self.scheduler:
            print(" Scheduler no disponible, tareas autonomas no configuradas")
            return
        
        try:
            self.scheduler.start()
            print(" Scheduler iniciado en segundo plano")
            
            # Programar resumen diario a las 21:00 (21:00)
            self.scheduler.schedule_daily_summary(hour=21, minute=0)
            print(" Resumen diario programado para las 21:00")
            
            # Programar tareas autonomas (correos, noticias, organizacion)
            self.scheduler.schedule_autonomous_tasks()
            print(" Tareas autonomas programadas")
            
        except Exception as e:
            print(f" Error configurando tareas autonomas: {e}")
    
    def get_weather(self, **kwargs) -> str:
        try:
            api_key = config.weather_api_key
            if not api_key:
                return " No configuraste la API del clima"
            city = config.saturday_city
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = get_with_retry(url, timeout=10)
            if response and response.status_code == 200:
                data = response.json()
                return f" El clima en {city} es {data['weather'][0]['description']} con {data['main']['temp']}oC"
            return " Error obteniendo el clima"
        except Exception as e:
            return f" Error: {str(e)}"
    
    def get_greeting(self, **kwargs) -> str:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos dias"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        return f"{saludo}! Soy Saturday, tu asistente personal. ?En que puedo ayudarte?"
    
    def get_help(self, **kwargs) -> str:
        return """ COMANDOS DE SATURDAY:

 TAREAS (Notion):
  - tareas - Tareas pendientes
  - crear tarea [nombre] - Crea una tarea
  - completar tarea [nombre] - Completa una tarea
  - eliminar tarea [nombre] - Elimina una tarea
  - tareas hoy - Tareas de hoy
  - tareas completadas - Tareas completadas

 NOTAS:
  - nota [texto] - Guarda una nota
  - ver notas - Muestra notas

 RECORDATORIOS:
  - recordatorio [texto] a las [hora] - Crea recordatorio
  - ver recordatorios - Muestra recordatorios
  - recordatorios hoy - Recordatorios de hoy

 CALENDARIO:
  - eventos - Eventos proximos
  - eventos hoy - Eventos de hoy
  - crear evento [titulo] el [fecha] a las [hora]

 EMAILS:
  - correos - Correos recientes
  - no leidos - Correos no leidos
  - enviar correo a [email] asunto [asunto]

 WHATSAPP:
  - envia WhatsApp [mensaje] - Envia mensaje de texto
  - envia voz WhatsApp [mensaje] - Envia mensaje de voz

 ESTADISTICAS:
  - estadisticas - Estadisticas de uso

 INFORMACIN:
  - hora - Hora actual
  - fecha - Fecha actual
  - clima - Clima
  
o NOTICIAS:
  - noticias - Noticias principales
  - noticias de [categoria] - Filtrar por categoria
  - buscar noticias [tema] - Buscar por tema
  - noticias resumen - Enviar resumen por WhatsApp

 OTROS:
  - hola - Saludo
  - ayuda - Esta ayuda"""
    
    # ============ TELEGRAM ============
    
    def send_to_telegram(self, text: str):
        """Envia un mensaje a Telegram si esta disponible"""
        if self.telegram and hasattr(self.telegram, 'send_message'):
            try:
                self.telegram.send_message(text)
            except Exception as e:
                print(f" Error enviando a Telegram: {e}")
    
    # ============ DELEGAR A MDULOS ============
    
    def get_tasks(self, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.get_tasks_formatted()
    
    def search_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.search_task(name)
    
    def create_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.create_task(name)
    
    def complete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.complete_task(name)
    
    def delete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.delete_task(name)
    
    def get_tasks_today(self, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.get_tasks_today()
    
    def get_completed_tasks(self, **kwargs) -> str:
        if not self.notion:
            return " Notion no esta configurado"
        return self.notion.get_completed_tasks()
    
    def create_note(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.create_note(text)
    
    def get_notes(self, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.get_notes()
    
    def search_notes(self, query: str = None, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.search_notes(query)
    
    def create_reminder(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.create_reminder(text)
    
    def get_reminders(self, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.get_reminders()
    
    def get_reminders_today(self, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.get_reminders_today()
    
    def get_stats(self, **kwargs) -> str:
        if not self.data:
            return " DataManager no disponible"
        return self.data.get_stats()
    
    # ------------------------------------------------------------------
    # BVEDA (memoria en Markdown)
    # ------------------------------------------------------------------

    def guardar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Guarda algo dicho/capturado en raw/ de la boveda."""
        if not self.vault:
            return " VaultManager no disponible"
        if not text:
            return "?Que quieres que guarde en la boveda?"
        path = self.vault.save_raw(text, source="voz" if kwargs.get("voz") else "chat")
        return f" Guardado en la boveda: {path}"

    def buscar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Busca un texto en toda la boveda."""
        if not self.vault:
            return " VaultManager no disponible"
        if not text:
            return "?Que quieres buscar en la boveda?"
        results = self.vault.search(text)
        if not results:
            return f"No encontre nada con '{text}' en la boveda."
        lines = [f" {len(results)} resultado(s) para '{text}':"]
        for r in results[:5]:
            lines.append(f"   {r['path']}: ...{r['snippet']}...")
        return "\n".join(lines)

    def estado_boveda(self, **kwargs) -> str:
        """Resumen de la boveda (cuantas notas hay en cada capa)."""
        if not self.vault:
            return " VaultManager no disponible"
        return self.vault.get_stats_text()

    def get_camera(self, **kwargs) -> str:
        """Obtiene imagen/estado de la camara"""
        if not self.camera:
            return " CameraManager no disponible"
        return self.camera.get_status()
    
    def get_system_info(self, **kwargs) -> str:
        """Obtiene informacion del sistema (CPU, RAM, disco)"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f" CPU: {cpu}% |  RAM: {mem.percent}% ({mem.used//1024//1024}GB/{mem.total//1024//1024}GB) | "
                    f" Disco: {disk.percent}% ({disk.used//1024//1024}GB/{disk.total//1024//1024}GB)")
        except ImportError:
            return " psutil no esta instalado en el backend"
        except Exception as e:
            return f" Error: {str(e)}"
    
    def get_events(self, **kwargs) -> str:
        if not self.calendar:
            return " CalendarManager no disponible"
        return self.calendar.get_events_formatted()
    
    def get_events_today(self, **kwargs) -> str:
        if not self.calendar:
            return " CalendarManager no disponible"
        return self.calendar.get_events_today_formatted()
    
    def create_event(self, text: str = None, **kwargs) -> str:
        if not self.calendar:
            return " CalendarManager no disponible"
        return self.calendar.create_event_from_text(text)
    
    def get_emails(self, **kwargs) -> str:
        if not self.email:
            return " EmailManager no disponible"
        return self.email.get_emails_formatted()
    
    def get_unread_emails(self, **kwargs) -> str:
        if not self.email:
            return " EmailManager no disponible"
        return self.email.get_unread_emails_formatted()
    
    def send_email(self, text: str = None, **kwargs) -> str:
        if not self.email:
            return " EmailManager no disponible"
        return self.email.send_email_from_text(text)
    
    # ============ WHATSAPP (CommunicationManager) ============
    
    def send_whatsapp(self, text: str = None, **kwargs) -> str:
        """Envia un mensaje por WhatsApp"""
        if not self.communication:
            return " CommunicationManager no disponible. Verifica la configuracion."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "?Que mensaje quieres enviar? Dime: 'envia WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envia WhatsApp", "enviar WhatsApp", "envia wsp", "enviar wsp", "whatsapp"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendi el mensaje. Dime: 'envia WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_message(text)
        
        if result.get('success'):
            return f" Mensaje enviado por WhatsApp: '{text}'"
        else:
            return f" Error al enviar WhatsApp: {result.get('error')}"
    
    def send_whatsapp_voice(self, text: str = None, **kwargs) -> str:
        """Envia un mensaje de voz por WhatsApp"""
        if not self.communication:
            return " CommunicationManager no disponible. Verifica la configuracion."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "?Que mensaje de voz quieres enviar? Dime: 'envia voz WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envia voz WhatsApp", "enviar voz WhatsApp", "voz WhatsApp", "whatsapp voz"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendi el mensaje. Dime: 'envia voz WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_voice(text)
        
        if result.get('success'):
            return f" Mensaje de voz enviado por WhatsApp: '{text}'"
        else:
            return f" Error al enviar voz WhatsApp: {result.get('error')}"
    
    def send_daily_summary(self, **kwargs) -> str:
        """Envia un resumen del dia por WhatsApp"""
        if not self.daily_summary:
            return " DailySummary no disponible"
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return " WhatsApp no configurado. Verifica WHATSAPP_NUMBER y WHATSAPP_API_KEY"
        
        result = self.daily_summary.send(via="whatsapp")
        
        if result.get('success'):
            msg = " Resumen del dia enviado por WhatsApp. Revisa tu telefono."
            if result.get('vault_path'):
                msg += f"\n Guardado en la boveda: {result['vault_path']}"
            return msg
        else:
            return f" Error al enviar resumen: {result.get('error')}"
        
    def open_spotify(self, **kwargs) -> str:
        """Abre Spotify Web"""
        if not self.spotify:
            return " Spotify no disponible"
        return self.spotify.open_spotify()

    def play_music(self, text: str = None, **kwargs) -> str:
        """Reproduce musica en Spotify"""
        if not self.spotify:
            return " Spotify no disponible"
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["reproduce", "reproducir", "pon", "toca", "play", "musica", "cancion", "cancion"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return self.spotify.play()
        
        return self.spotify.play(text)

    def pause_music(self, **kwargs) -> str:
        """Pausa la musica"""
        if not self.spotify:
            return " Spotify no disponible"
        return self.spotify.pause()

    def next_track(self, **kwargs) -> str:
        """Siguiente cancion"""
        if not self.spotify:
            return " Spotify no disponible"
        return self.spotify.next_track()

    def previous_track(self, **kwargs) -> str:
        """Cancion anterior"""
        if not self.spotify:
            return " Spotify no disponible"
        return self.spotify.previous_track()

    def current_track(self, **kwargs) -> str:
        """Muestra la cancion actual"""
        if not self.spotify:
            return " Spotify no disponible"
        return self.spotify.get_current_track()
    
    def get_news(self, text: str = None, **kwargs) -> str:
        """Obtiene noticias principales"""
        if not self.news or not self.news.is_available():
            return " Noticias no disponible. Verifica NEWS_API_KEY."
        
        # Detectar categoria
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
            return " Noticias no disponible. Verifica NEWS_API_KEY."
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["buscar noticias", "buscar noticia", "noticias de", "noticias sobre", "buscar"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return "?Que tema quieres buscar? Dime: 'buscar noticias [tema]'"
        
        articles = self.news.search_news(text, limit=5)
        return self.news.format_news(articles)

    def get_news_summary(self, **kwargs) -> str:
        """Envia un resumen de noticias por WhatsApp"""
        if not self.news or not self.news.is_available():
            return " Noticias no disponible. Verifica NEWS_API_KEY."
        
        articles = self.news.get_top_headlines(limit=5)
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return self.news.format_news(articles)
        
        # Enviar por WhatsApp
        message = self.news.format_news_for_whatsapp(articles)
        result = self.communication.send_whatsapp_message(message)
        
        if result.get('success'):
            return "o Resumen de noticias enviado por WhatsApp"
        else:
            return self.news.format_news(articles)



