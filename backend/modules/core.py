# modules/core.py - Nucleo de Saturday COMPLETO
import os
from datetime import datetime
from typing import Dict, Any
import networkx as nx
from modules.http_utils import get_with_retry
from modules.config import config

# Importar mÃ³dulos
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
    from modules.communication import CommunicationManager
    COMMUNICATION_AVAILABLE = True
    print("âœ… CommunicationManager importado correctamente")
except ImportError as e:
    COMMUNICATION_AVAILABLE = False
    print(f"âš ï¸ CommunicationManager no disponible: {e}")

try:
    from modules.daily_summary import DailySummary
    DAILY_SUMMARY_AVAILABLE = True
except ImportError:
    DAILY_SUMMARY_AVAILABLE = False
    print("âš ï¸ DailySummary no disponible")
    
try:
    from modules.scheduler import Scheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("âš ï¸ Scheduler no disponible")
    
try:
    from modules.spotify_manager import SpotifyManager
    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False
    print("âš ï¸ SpotifyManager no disponible")
    
try:
    from modules.news_manager import NewsManager
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("âš ï¸ NewsManager no disponible")
    
try:
    from modules.camera_manager import CameraManager
    CAMERA_AVAILABLE = True
    print("âœ… CameraManager importado correctamente")
except ImportError as e:
    CAMERA_AVAILABLE = False
    print(f"âš ï¸ CameraManager no disponible: {e}")

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
    """NÃºcleo de inteligencia de Saturday"""

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
        print("ðŸ§  Inicializando nÃºcleo de Saturday...")
        
        # Inicializar DataManager
        self.data = None
        if DATA_AVAILABLE:
            try:
                self.data = DataManager()
                print("âœ… DataManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando DataManager: {e}")
        
        # Inicializar VaultManager (memoria en Markdown, "bÃ³veda/")
        self.vault = None
        if VAULT_AVAILABLE:
            try:
                self.vault = VaultManager()
                print("âœ… VaultManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando VaultManager: {e}")

        # Motor de interpretaciÃ³n de intenciones (sinÃ³nimos + fuzzy matching,
        # ver modules/intent_engine.py)
        self.intent_engine = build_default_engine()

        # Inicializar Notion
        self.notion = None
        if NOTION_AVAILABLE:
            try:
                if config.notion_api_key and config.notion_db_id:
                    self.notion = NotionManager(config.notion_api_key, config.notion_db_id)
                    print("âœ… Notion conectado")
                else:
                    print("âš ï¸ NOTION_API_KEY o NOTION_DB_ID no configurados")
            except Exception as e:
                print(f"âš ï¸ Error conectando a Notion: {e}")
        
        # Inicializar VoiceManager
        self.voice = None
        if VOICE_AVAILABLE:
            try:
                self.voice = VoiceManager()
                print("âœ… VoiceManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando VoiceManager: {e}")
        
        # Inicializar Calendar
        self.calendar = None
        if CALENDAR_AVAILABLE:
            try:
                self.calendar = CalendarManager()
                print("âœ… CalendarManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando CalendarManager: {e}")
        
        # Inicializar Email
        self.email = None
        if EMAIL_AVAILABLE:
            try:
                self.email = EmailManager()
                print("âœ… EmailManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando EmailManager: {e}")
        
        # Inicializar Telegram
        self.telegram = None
        if TELEGRAM_AVAILABLE:
            try:
                if config.telegram_bot_token:
                    self.telegram = TelegramBot(self, config.telegram_bot_token)
                    print("âœ… TelegramBot inicializado")
                else:
                    print("âš ï¸ TELEGRAM_BOT_TOKEN no configurado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando TelegramBot: {e}")
        
        # Inicializar Communication (WhatsApp)
        self.communication = None
        if COMMUNICATION_AVAILABLE:
            try:
                self.communication = CommunicationManager()
                print("âœ… CommunicationManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando CommunicationManager: {e}")
                
        self.daily_summary = None
        if DAILY_SUMMARY_AVAILABLE:
            try:
                self.daily_summary = DailySummary(self)
                print("âœ… DailySummary inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando DailySummary: {e}")
                
        self.scheduler = None
        if SCHEDULER_AVAILABLE:
            try:
                self.scheduler = Scheduler(self)
                print("âœ… Scheduler inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando Scheduler: {e}")
        
        self.spotify = None
        if SPOTIFY_AVAILABLE:
            try:
                self.spotify = SpotifyManager()
                print("âœ… SpotifyManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando SpotifyManager: {e}")
                
        self.news = None
        if NEWS_AVAILABLE:
            try:
                self.news = NewsManager()
                print("âœ… NewsManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando NewsManager: {e}")
                
        # Inicializar CÃ¡mara
        self.camera = None
        if CAMERA_AVAILABLE:
            try:
                self.camera = CameraManager()
                print("âœ… CameraManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando CameraManager: {e}")
        
        # Inicializar ConversationManager (memoria conversacional)
        self.conversation = None
        if CONVERSATION_AVAILABLE:
            try:
                self.conversation = ConversationManager()
                print("âœ… ConversationManager inicializado")
            except Exception as e:
                print(f"âš ï¸ Error inicializando ConversationManager: {e}")
        
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
        
        # Auto-iniciar scheduler y programar tareas autÃ³nomas
        self._setup_autonomous_tasks()
        
        print("âœ… NÃºcleo inicializado correctamente")
    
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
            # InformaciÃ³n
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
            
            # EstadÃ­sticas
            "estadisticas": self.get_stats,
            "system_info": self.get_system_info,
            
            # ComunicaciÃ³n (WhatsApp)
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
            
            # CÃ¡mara
            "get_camera": self.get_camera,

            # BÃ³veda (memoria en Markdown)
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
        Procesa la intenciÃ³n del usuario con contexto conversacional.
        Si chat_id se provee, usa memoria de conversaciÃ³n.
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
                response = "No entendí tu petición. ¿Puedes repetirla o decir 'ayuda' para ver qué puedo hacer?"
            
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
        # IntenciÃ³n "abrir_noticias": solo indica al frontend cambiar vista
        # ------------------------------------------------------------
        if match.meta.get("navigate"):
            response = "Abriendo el panel de noticias ðŸ“°"
            if chat_id and self.conversation:
                self.conversation.add_assistant_message(chat_id, response, intent)
            return {
                "intent": intent,
                "response": response,
                "action": True,
                "navigate": match.meta["navigate"],
            }

        # ------------------------------------------------------------
        # Resto de intenciones: se ejecutan a travÃ©s del knowledge_graph
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
                    
                    self.send_to_telegram(f"ðŸ“± Interfaz: {text}")
                    self.send_to_telegram(f"ðŸŸ£ Saturday: {result}")
                    return {"intent": intent, "response": result, "action": True}
                except Exception as e:
                    return {"intent": "error", "response": f"âŒ Error: {str(e)}", "action": False}

        return {"intent": "general", "response": "No entendÃ­ tu peticiÃ³n. Â¿Puedes repetirla?", "action": False}

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
        Agrega follow-ups naturales segÃºn la intenciÃ³n.
        """
        if not self.conversation:
            return result
        
        ctx = self.conversation.get_context(chat_id)
        
        # Follow-ups naturales segÃºn intenciÃ³n
        followups = {
            "clima": " Â¿Te parece si te aviso si cambia el clima?",
            "hora": " Â¿Necesitas que te recuerde algo para despuÃ©s?",
            "fecha": " Â¿Tienes algÃºn evento hoy?",
            "tareas": " Â¿Quieres que te ayude con alguna?",
            "noticias": " Â¿Te interesa algÃºn tema en particular?",
            "correos": " Â¿Quieres que responda alguno?",
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
            "clima": "El clima es algo que cambia seguido. Â¿Quieres que te avise si hay lluvia pronosticada?",
            "hora": "La hora no cambia mucho ðŸ˜„. Â¿Necesitas programar algo?",
            "fecha": "Hoy es " + datetime.now().strftime("%A %d de %B") + ". Â¿Tienes planes?",
            "tareas": "Â¿Quieres que te muestre las tareas pendientes o creemos una nueva?",
            "noticias": "Â¿Hay algÃºn tema que te interese mÃ¡s? Puedo buscar noticias especÃ­ficas.",
            "correos": "Â¿Quieres que revise tus correos no leÃ­dos?",
            "spotify": "Â¿Quieres que ponga algo de mÃºsica?",
        }
        
        response = followup_responses.get(last_topic, 
            f"EstÃ¡bamos hablando de {last_topic}. Â¿QuÃ© quieres saber?")
        
        self.conversation.add_assistant_message(chat_id, response, "followup")
        
        return {"intent": "followup", "response": response, "action": False}
    
    # ============ ACCIONES BÃSICAS ============
    
    def get_status(self, **kwargs) -> str:
        """Estado general de Saturday"""
        modules = []
        
        # Verificar mÃ³dulos
        if self.notion:
            modules.append("âœ… Notion")
        else:
            modules.append("âŒ Notion")
        
        if self.calendar:
            modules.append("âœ… Calendario")
        else:
            modules.append("âŒ Calendario")
        
        if self.email:
            modules.append("âœ… Correos")
        else:
            modules.append("âŒ Correos")
        
        if self.communication:
            modules.append("âœ… WhatsApp")
        else:
            modules.append("âŒ WhatsApp")
        
        if self.news:
            modules.append("âœ… Noticias")
        else:
            modules.append("âŒ Noticias")
        
        if self.voice:
            modules.append("âœ… Voz (TTS/STT)")
        else:
            modules.append("âŒ Voz")
        
        if self.scheduler:
            scheduler_status = "ðŸŸ¢ Activo" if self.scheduler.is_running else "ðŸ”´ Detenido"
            modules.append(f"â° Scheduler: {scheduler_status}")
        
        if self.conversation:
            modules.append("âœ… Memoria conversacional")
        else:
            modules.append("âŒ Memoria conversacional")
        
        # InformaciÃ³n del sistema
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            sys_info = f"ðŸ’» CPU: {cpu}% | RAM: {mem.percent}%"
        except (ImportError, Exception):
            sys_info = ""
        
        response = "ðŸŸ£ **ESTADO DE SATURDAY**\n\n"
        response += "\n".join(modules)
        if sys_info:
            response += f"\n\n{sys_info}"
        
        return response
    
    def get_time(self, **kwargs) -> str:
        ahora = datetime.now()
        return f"Son las {ahora.strftime('%I:%M %p')}"
    
    def get_date(self, **kwargs) -> str:
        ahora = datetime.now()
        dias = ["lunes", "martes", "miÃ©rcoles", "jueves", "viernes", "sÃ¡bado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", 
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"Hoy es {dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year}"
    
    def _setup_autonomous_tasks(self):
        """Configura tareas autÃ³nomas del scheduler"""
        if not self.scheduler:
            print("âš ï¸ Scheduler no disponible, tareas autÃ³nomas no configuradas")
            return
        
        try:
            self.scheduler.start()
            print("â° Scheduler iniciado en segundo plano")
            
            # Programar resumen diario a las 21:00 (9 PM)
            self.scheduler.schedule_daily_summary(hour=21, minute=0)
            print("ðŸ“‹ Resumen diario programado para las 21:00")
            
            # Programar tareas autÃ³nomas (correos, noticias, organizaciÃ³n)
            self.scheduler.schedule_autonomous_tasks()
            print("ðŸ¤– Tareas autÃ³nomas programadas")
            
        except Exception as e:
            print(f"âš ï¸ Error configurando tareas autÃ³nomas: {e}")
    
    def get_weather(self, **kwargs) -> str:
        try:
            api_key = config.weather_api_key
            if not api_key:
                return "âŒ No configuraste la API del clima"
            city = config.saturday_city
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = get_with_retry(url, timeout=10)
            if response and response.status_code == 200:
                data = response.json()
                return f"ðŸŒ¤ï¸ El clima en {city} es {data['weather'][0]['description']} con {data['main']['temp']}Â°C"
            return "âŒ Error obteniendo el clima"
        except Exception as e:
            return f"âŒ Error: {str(e)}"
    
    def get_greeting(self, **kwargs) -> str:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos dÃ­as"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        return f"{saludo}! Soy Saturday, tu asistente personal. Â¿En quÃ© puedo ayudarte?"
    
    def get_help(self, **kwargs) -> str:
        return """ðŸŸ£ COMANDOS DE SATURDAY:

ðŸ“‹ TAREAS (Notion):
  â€¢ tareas - Tareas pendientes
  â€¢ crear tarea [nombre] - Crea una tarea
  â€¢ completar tarea [nombre] - Completa una tarea
  â€¢ eliminar tarea [nombre] - Elimina una tarea
  â€¢ tareas hoy - Tareas de hoy
  â€¢ tareas completadas - Tareas completadas

ðŸ“ NOTAS:
  â€¢ nota [texto] - Guarda una nota
  â€¢ ver notas - Muestra notas

â° RECORDATORIOS:
  â€¢ recordatorio [texto] a las [hora] - Crea recordatorio
  â€¢ ver recordatorios - Muestra recordatorios
  â€¢ recordatorios hoy - Recordatorios de hoy

ðŸ“… CALENDARIO:
  â€¢ eventos - Eventos prÃ³ximos
  â€¢ eventos hoy - Eventos de hoy
  â€¢ crear evento [tÃ­tulo] el [fecha] a las [hora]

ðŸ“§ EMAILS:
  â€¢ correos - Correos recientes
  â€¢ no leÃ­dos - Correos no leÃ­dos
  â€¢ enviar correo a [email] asunto [asunto]

ðŸ“± WHATSAPP:
  â€¢ envÃ­a WhatsApp [mensaje] - EnvÃ­a mensaje de texto
  â€¢ envÃ­a voz WhatsApp [mensaje] - EnvÃ­a mensaje de voz

ðŸ“Š ESTADÃSTICAS:
  â€¢ estadisticas - EstadÃ­sticas de uso

ðŸ• INFORMACIÃ“N:
  â€¢ hora - Hora actual
  â€¢ fecha - Fecha actual
  â€¢ clima - Clima
  
ðŸ“° NOTICIAS:
  â€¢ noticias - Noticias principales
  â€¢ noticias de [categorÃ­a] - Filtrar por categorÃ­a
  â€¢ buscar noticias [tema] - Buscar por tema
  â€¢ noticias resumen - Enviar resumen por WhatsApp

ðŸ’¬ OTROS:
  â€¢ hola - Saludo
  â€¢ ayuda - Esta ayuda"""
    
    # ============ TELEGRAM ============
    
    def send_to_telegram(self, text: str):
        """EnvÃ­a un mensaje a Telegram si estÃ¡ disponible"""
        if self.telegram and hasattr(self.telegram, 'send_message'):
            try:
                self.telegram.send_message(text)
            except Exception as e:
                print(f"âš ï¸ Error enviando a Telegram: {e}")
    
    # ============ DELEGAR A MÃ“DULOS ============
    
    def get_tasks(self, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.get_tasks_formatted()
    
    def search_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.search_task(name)
    
    def create_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.create_task(name)
    
    def complete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.complete_task(name)
    
    def delete_task(self, name: str = None, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.delete_task(name)
    
    def get_tasks_today(self, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.get_tasks_today()
    
    def get_completed_tasks(self, **kwargs) -> str:
        if not self.notion:
            return "âŒ Notion no estÃ¡ configurado"
        return self.notion.get_completed_tasks()
    
    def create_note(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.create_note(text)
    
    def get_notes(self, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.get_notes()
    
    def search_notes(self, query: str = None, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.search_notes(query)
    
    def create_reminder(self, text: str = None, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.create_reminder(text)
    
    def get_reminders(self, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.get_reminders()
    
    def get_reminders_today(self, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.get_reminders_today()
    
    def get_stats(self, **kwargs) -> str:
        if not self.data:
            return "âŒ DataManager no disponible"
        return self.data.get_stats()
    
    # ------------------------------------------------------------------
    # BÃ“VEDA (memoria en Markdown)
    # ------------------------------------------------------------------

    def guardar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Guarda algo dicho/capturado en raw/ de la bÃ³veda."""
        if not self.vault:
            return "âŒ VaultManager no disponible"
        if not text:
            return "Â¿QuÃ© quieres que guarde en la bÃ³veda?"
        path = self.vault.save_raw(text, source="voz" if kwargs.get("voz") else "chat")
        return f"âœ… Guardado en la bÃ³veda: {path}"

    def buscar_en_boveda(self, text: str = None, **kwargs) -> str:
        """Busca un texto en toda la bÃ³veda."""
        if not self.vault:
            return "âŒ VaultManager no disponible"
        if not text:
            return "Â¿QuÃ© quieres buscar en la bÃ³veda?"
        results = self.vault.search(text)
        if not results:
            return f"No encontrÃ© nada con '{text}' en la bÃ³veda."
        lines = [f"ðŸ” {len(results)} resultado(s) para '{text}':"]
        for r in results[:5]:
            lines.append(f"  ðŸ“„ {r['path']}: ...{r['snippet']}...")
        return "\n".join(lines)

    def estado_boveda(self, **kwargs) -> str:
        """Resumen de la bÃ³veda (cuÃ¡ntas notas hay en cada capa)."""
        if not self.vault:
            return "âŒ VaultManager no disponible"
        return self.vault.get_stats_text()

    def get_camera(self, **kwargs) -> str:
        """Obtiene imagen/estado de la cÃ¡mara"""
        if not self.camera:
            return "âŒ CameraManager no disponible"
        return self.camera.get_status()
    
    def get_system_info(self, **kwargs) -> str:
        """Obtiene informaciÃ³n del sistema (CPU, RAM, disco)"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return (f"ðŸ’» CPU: {cpu}% | ðŸ“Ÿ RAM: {mem.percent}% ({mem.used//1024//1024}GB/{mem.total//1024//1024}GB) | "
                    f"ðŸ’¿ Disco: {disk.percent}% ({disk.used//1024//1024}GB/{disk.total//1024//1024}GB)")
        except ImportError:
            return "âŒ psutil no estÃ¡ instalado en el backend"
        except Exception as e:
            return f"âŒ Error: {str(e)}"
    
    def get_events(self, **kwargs) -> str:
        if not self.calendar:
            return "âŒ CalendarManager no disponible"
        return self.calendar.get_events_formatted()
    
    def get_events_today(self, **kwargs) -> str:
        if not self.calendar:
            return "âŒ CalendarManager no disponible"
        return self.calendar.get_events_today_formatted()
    
    def create_event(self, text: str = None, **kwargs) -> str:
        if not self.calendar:
            return "âŒ CalendarManager no disponible"
        return self.calendar.create_event_from_text(text)
    
    def get_emails(self, **kwargs) -> str:
        if not self.email:
            return "âŒ EmailManager no disponible"
        return self.email.get_emails_formatted()
    
    def get_unread_emails(self, **kwargs) -> str:
        if not self.email:
            return "âŒ EmailManager no disponible"
        return self.email.get_unread_emails_formatted()
    
    def send_email(self, text: str = None, **kwargs) -> str:
        if not self.email:
            return "âŒ EmailManager no disponible"
        return self.email.send_email_from_text(text)
    
    # ============ WHATSAPP (CommunicationManager) ============
    
    def send_whatsapp(self, text: str = None, **kwargs) -> str:
        """EnvÃ­a un mensaje por WhatsApp"""
        if not self.communication:
            return "âŒ CommunicationManager no disponible. Verifica la configuraciÃ³n."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "Â¿QuÃ© mensaje quieres enviar? Dime: 'envÃ­a WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envÃ­a WhatsApp", "enviar WhatsApp", "envÃ­a wsp", "enviar wsp", "whatsapp"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendÃ­ el mensaje. Dime: 'envÃ­a WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_message(text)
        
        if result.get('success'):
            return f"ðŸ“± Mensaje enviado por WhatsApp: '{text}'"
        else:
            return f"âŒ Error al enviar WhatsApp: {result.get('error')}"
    
    def send_whatsapp_voice(self, text: str = None, **kwargs) -> str:
        """EnvÃ­a un mensaje de voz por WhatsApp"""
        if not self.communication:
            return "âŒ CommunicationManager no disponible. Verifica la configuraciÃ³n."
        
        if not text:
            text = kwargs.get("text", "")
        if not text:
            return "Â¿QuÃ© mensaje de voz quieres enviar? Dime: 'envÃ­a voz WhatsApp [mensaje]'"
        
        # Limpiar el comando del texto
        for word in ["envÃ­a voz WhatsApp", "enviar voz WhatsApp", "voz WhatsApp", "whatsapp voz"]:
            text = text.replace(word, "").strip()
        
        if not text:
            return "No entendÃ­ el mensaje. Dime: 'envÃ­a voz WhatsApp [mensaje]'"
        
        result = self.communication.send_whatsapp_voice(text)
        
        if result.get('success'):
            return f"ðŸŽ¤ Mensaje de voz enviado por WhatsApp: '{text}'"
        else:
            return f"âŒ Error al enviar voz WhatsApp: {result.get('error')}"
    
    def send_daily_summary(self, **kwargs) -> str:
        """EnvÃ­a un resumen del dÃ­a por WhatsApp"""
        if not self.daily_summary:
            return "âŒ DailySummary no disponible"
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return "âŒ WhatsApp no configurado. Verifica WHATSAPP_NUMBER y WHATSAPP_API_KEY"
        
        result = self.daily_summary.send(via="whatsapp")
        
        if result.get('success'):
            msg = "ðŸ“‹ Resumen del dÃ­a enviado por WhatsApp. Revisa tu telÃ©fono."
            if result.get('vault_path'):
                msg += f"\nðŸ—‚ï¸ Guardado en la bÃ³veda: {result['vault_path']}"
            return msg
        else:
            return f"âŒ Error al enviar resumen: {result.get('error')}"
        
    def open_spotify(self, **kwargs) -> str:
        """Abre Spotify Web"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        return self.spotify.open_spotify()

    def play_music(self, text: str = None, **kwargs) -> str:
        """Reproduce mÃºsica en Spotify"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["reproduce", "reproducir", "pon", "toca", "play", "mÃºsica", "canciÃ³n", "cancion"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return self.spotify.play()
        
        return self.spotify.play(text)

    def pause_music(self, **kwargs) -> str:
        """Pausa la mÃºsica"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        return self.spotify.pause()

    def next_track(self, **kwargs) -> str:
        """Siguiente canciÃ³n"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        return self.spotify.next_track()

    def previous_track(self, **kwargs) -> str:
        """CanciÃ³n anterior"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        return self.spotify.previous_track()

    def current_track(self, **kwargs) -> str:
        """Muestra la canciÃ³n actual"""
        if not self.spotify:
            return "âŒ Spotify no disponible"
        return self.spotify.get_current_track()
    
    def get_news(self, text: str = None, **kwargs) -> str:
        """Obtiene noticias principales"""
        if not self.news or not self.news.is_available():
            return "âŒ Noticias no disponible. Verifica NEWS_API_KEY."
        
        # Detectar categorÃ­a
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
            return "âŒ Noticias no disponible. Verifica NEWS_API_KEY."
        
        if not text:
            text = kwargs.get("text", "")
        
        # Limpiar el comando
        for word in ["buscar noticias", "buscar noticia", "noticias de", "noticias sobre", "buscar"]:
            if text:
                text = text.replace(word, "").strip()
        
        if not text:
            return "Â¿QuÃ© tema quieres buscar? Dime: 'buscar noticias [tema]'"
        
        articles = self.news.search_news(text, limit=5)
        return self.news.format_news(articles)

    def get_news_summary(self, **kwargs) -> str:
        """EnvÃ­a un resumen de noticias por WhatsApp"""
        if not self.news or not self.news.is_available():
            return "âŒ Noticias no disponible. Verifica NEWS_API_KEY."
        
        articles = self.news.get_top_headlines(limit=5)
        
        if not self.communication or not self.communication.whatsapp_enabled:
            return self.news.format_news(articles)
        
        # Enviar por WhatsApp
        message = self.news.format_news_for_whatsapp(articles)
        result = self.communication.send_whatsapp_message(message)
        
        if result.get('success'):
            return "ðŸ“° Resumen de noticias enviado por WhatsApp"
        else:
            return self.news.format_news(articles)



