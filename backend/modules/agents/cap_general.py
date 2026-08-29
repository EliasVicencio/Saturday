# agents/cap_general.py - Agente general: chat, preguntas, reflexiones
import time
from .base import BaseAgent, AgentResult


class GeneralAgent(BaseAgent):
    name = "general"
    description = "Conversacion general, preguntas, reflexiones, explicaciones"
    tools = []

    def can_handle(self, text: str) -> float:
        text_lower = text.lower().strip()
        # Si no matchea otra capability, este es el default
        keywords = [
            "que es", "como funciona", "explica", "opinion", "pensar",
            "ayuda", "hola", "buenos dias", "buenas tardes", "gracias",
            "que opinas", "que piensas", "conversa", "habla",
        ]
        for kw in keywords:
            if kw in text_lower:
                return 0.9
        return 0.3  # Bajo score porque es el fallback

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = time.time()

        # Inyectar contexto de memoria
        memory_context = ""
        if self.core and self.core.memory_retriever:
            memory_context = self.core.memory_retriever.before_respond(text, chat_id)

        full_context = text
        if memory_context:
            full_context = memory_context + "\n\nMensaje del usuario: " + text

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
