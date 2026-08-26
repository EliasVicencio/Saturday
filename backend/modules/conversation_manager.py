# modules/conversation_manager.py - Memoria conversacional de Saturday
"""
Sistema de memoria que mantiene contexto entre mensajes.
Permite que Saturday recuerde qué habló, pregunte de seguimiento,
y responda de forma natural (no solo comandos → respuestas).
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Message:
    role: str  # "user" o "assistant"
    text: str
    intent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationContext:
    """Contexto de una conversación (por chat_id)"""
    chat_id: int
    messages: List[Message] = field(default_factory=list)
    last_intent: str = ""
    last_topic: str = ""  # tema último (ej: "clima", "tareas")
    pending_question: str = ""  # pregunta que Saturday quedó debiendo
    user_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_message(self, role: str, text: str, intent: str = ""):
        msg = Message(role=role, text=text, intent=intent)
        self.messages.append(msg)
        self.last_active = datetime.now().isoformat()
        # Mantener solo los últimos 20 mensajes
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
    
    def get_recent_context(self, n: int = 5) -> List[Dict]:
        """Retorna los últimos n mensajes como dicts"""
        return [asdict(m) for m in self.messages[-n:]]
    
    def get_last_user_message(self) -> Optional[str]:
        """Retorna el último mensaje del usuario"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.text
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Retorna el último mensaje del asistente"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.text
        return None


class ConversationManager:
    """
    Gestiona conversaciones por chat_id.
    Mantiene memoria de los últimos 30 minutos de conversación.
    """
    
    EXPIRY_MINUTES = 30  # Conversaciones expiran después de 30 min sin actividad
    SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "conversations.json")
    
    def __init__(self):
        self._conversations: Dict[int, ConversationContext] = {}
        self._load()
    
    def _load(self):
        """Carga conversaciones desde disco"""
        try:
            if os.path.exists(self.SAVE_PATH):
                with open(self.SAVE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for chat_id_str, ctx_data in data.items():
                    chat_id = int(chat_id_str)
                    ctx = ConversationContext(
                        chat_id=chat_id,
                        last_intent=ctx_data.get("last_intent", ""),
                        last_topic=ctx_data.get("last_topic", ""),
                        pending_question=ctx_data.get("pending_question", ""),
                        user_name=ctx_data.get("user_name", ""),
                        created_at=ctx_data.get("created_at", ""),
                        last_active=ctx_data.get("last_active", ""),
                    )
                    for msg_data in ctx_data.get("messages", []):
                        ctx.messages.append(Message(**msg_data))
                    self._conversations[chat_id] = ctx
        except Exception as e:
            print(f"⚠️ Error cargando conversaciones: {e}")
    
    def _save(self):
        """Guarda conversaciones en disco"""
        try:
            os.makedirs(os.path.dirname(self.SAVE_PATH), exist_ok=True)
            data = {}
            for chat_id, ctx in self._conversations.items():
                data[str(chat_id)] = {
                    "chat_id": ctx.chat_id,
                    "messages": [asdict(m) for m in ctx.messages],
                    "last_intent": ctx.last_intent,
                    "last_topic": ctx.last_topic,
                    "pending_question": ctx.pending_question,
                    "user_name": ctx.user_name,
                    "created_at": ctx.created_at,
                    "last_active": ctx.last_active,
                }
            with open(self.SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando conversaciones: {e}")
    
    def get_context(self, chat_id: int) -> ConversationContext:
        """Obtiene o crea el contexto de un chat"""
        if chat_id in self._conversations:
            ctx = self._conversations[chat_id]
            # Verificar si expiró
            last_active = datetime.fromisoformat(ctx.last_active)
            if datetime.now() - last_active > timedelta(minutes=self.EXPIRY_MINUTES):
                # Resetear conversación
                ctx = ConversationContext(chat_id=chat_id)
                self._conversations[chat_id] = ctx
        else:
            ctx = ConversationContext(chat_id=chat_id)
            self._conversations[chat_id] = ctx
        return ctx
    
    def add_user_message(self, chat_id: int, text: str, intent: str = ""):
        """Registra un mensaje del usuario"""
        ctx = self.get_context(chat_id)
        ctx.add_message("user", text, intent)
        self._save()
    
    def add_assistant_message(self, chat_id: int, text: str, intent: str = ""):
        """Registra un mensaje del asistente"""
        ctx = self.get_context(chat_id)
        ctx.add_message("assistant", text, intent)
        ctx.last_intent = intent
        self._save()
    
    def set_pending_question(self, chat_id: int, question: str):
        """Registra una pregunta pendiente de seguimiento"""
        ctx = self.get_context(chat_id)
        ctx.pending_question = question
        self._save()
    
    def clear_pending_question(self, chat_id: int):
        """Limpia la pregunta pendiente"""
        ctx = self.get_context(chat_id)
        ctx.pending_question = ""
        self._save()
    
    def set_user_name(self, chat_id: int, name: str):
        """Guarda el nombre del usuario"""
        ctx = self.get_context(chat_id)
        ctx.user_name = name
        self._save()
    
    def is_followup(self, text: str) -> bool:
        """Detecta si el usuario está preguntando de seguimiento"""
        followup_patterns = [
            "y eso", "cuéntame más", "cuéntame mas", "más info", "mas info",
            "por qué", "por que", "cómo", "como", "cuándo", "cuando",
            "dónde", "donde", "quién", "quien", "cuánto", "cuanto",
            "explícame", "explicame", "detalles", "detallame",
            "y ahora", "y qué más", "y que mas", "sigue", "continúa",
            "cuéntame", "cuantame", "háblame", "hablame",
        ]
        text_lower = text.lower().strip()
        return any(p in text_lower for p in followup_patterns)
    
    def get_context_hint(self, chat_id: int) -> str:
        """
        Retorna un hint de contexto para enriquecer la respuesta.
        Ej: "El usuario preguntó por el clima hace 2 minutos"
        """
        ctx = self.get_context(chat_id)
        
        if ctx.pending_question:
            return f"Nota: El usuario tiene una pregunta pendiente: '{ctx.pending_question}'"
        
        if ctx.last_topic:
            last_msg_time = ctx.last_active
            try:
                last_dt = datetime.fromisoformat(last_msg_time)
                diff = datetime.now() - last_dt
                minutes = int(diff.total_seconds() / 60)
                if minutes < 5:
                    return f"Contexto: Último tema '{ctx.last_topic}' (hace {minutes} min)"
            except:
                pass
        
        return ""
    
    def get_stats(self, chat_id: int) -> Dict:
        """Estadísticas de la conversación"""
        ctx = self.get_context(chat_id)
        user_msgs = [m for m in ctx.messages if m.role == "user"]
        assistant_msgs = [m for m in ctx.messages if m.role == "assistant"]
        intents_used = list(set(m.intent for m in assistant_msgs if m.intent))
        
        return {
            "total_messages": len(ctx.messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "intents_used": intents_used,
            "last_topic": ctx.last_topic,
            "created_at": ctx.created_at,
            "last_active": ctx.last_active,
        }
