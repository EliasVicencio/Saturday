# agents/cap_general.py - Agente general: chat, preguntas, reflexiones
import time
from .base import BaseAgent, AgentResult, keyword_score


class GeneralAgent(BaseAgent):
    name = "general"
    description = "Conversacion general, preguntas, reflexiones, explicaciones"
    tools = []

    def can_handle(self, text: str) -> float:
        text_lower = text.lower().strip()
        # Si no matchea otra capability, este es el default
        keywords = {
            "que es": 0.9, "como funciona": 0.9, "explica": 0.9, "opinion": 0.9, "pensar": 0.9,
            "ayuda": 0.9, "hola": 0.9, "buenos dias": 0.9, "buenas tardes": 0.9, "gracias": 0.9,
            "que opinas": 0.9, "que piensas": 0.9, "conversa": 0.9, "habla": 0.9,
        }
        score = keyword_score(text_lower, keywords)
        return score if score > 0 else 0.3  # Bajo score porque es el fallback

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = time.time()

        # Inyectar contexto de memoria
        memory_context = ""
        if self.core and self.core.memory_retriever:
            memory_context = self.core.memory_retriever.before_respond(text, chat_id)

        # Inyectar contexto de rutina (qué suele pedir el usuario a esta hora)
        routine_context = ""
        if self.core and self.core.memory_retriever and getattr(self.core, "routines", None):
            try:
                routine_context = self.core.memory_retriever.format_routine_context(
                    self.core.routines.get_routines()
                )
            except Exception:
                routine_context = ""

        full_context = text
        extra = "\n\n".join(c for c in (memory_context, routine_context) if c)
        if extra:
            full_context = extra + "\n\nMensaje del usuario: " + text

        # Extraer y guardar recuerdos
        if self.core and self.core.memory_summarizer:
            self.core.memory_summarizer.process_and_save(text, chat_id)

        # LLM
        response = ""
        if self.core and self.core.gemini:
            response = self.core.gemini.chat(full_context, chat_id=chat_id) or ""

        if not response:
            response = "No pude procesar tu mensaje. Intenta de nuevo."

        duration = (time.time() - start) * 1000
        return AgentResult(response=response, agent=self.name, duration_ms=duration)
