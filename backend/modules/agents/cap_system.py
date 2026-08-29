# agents/cap_system.py - Agente de sistema: comandos SO, archivos, procesos, correo
import time
from .base import BaseAgent, AgentResult


class SystemAgent(BaseAgent):
    name = "system"
    description = "Control del sistema, archivos, procesos, configuracion, correo"
    tools = ["get_time", "get_system_stats"]
    destructive_actions = ["execute_command"]

    def can_handle(self, text: str) -> float:
        text_lower = text.lower()
        keywords = [
            "hora", "fecha", "hora exacta", "que hora es", "que fecha es",
            "sistema", "cpu", "ram", "disco", "procesos", "servidor",
            "reiniciar", "apagar", "actualizar", "instalar",
            "archivo", "carpeta", "directorio", "listar", "eliminar",
            "abrir", "cerrar", "ejecutar", "correr",
            "correo", "correos", "email", "enviar correo", "revisar correo",
        ]
        score = 0.0
        for kw in keywords:
            if kw in text_lower:
                score = max(score, 0.85)
                break
        return score

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = time.time()
        tools_log = []
        text_lower = text.lower()

        # Hora / fecha
        if any(kw in text_lower for kw in ["hora", "que hora es", "hora exacta"]):
            result = self.call_tool("get_time")
            tools_log.append({"tool": "get_time", "args": {}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        if any(kw in text_lower for kw in ["fecha", "que fecha es", "que dia es"]):
            result = self.call_tool("get_time")
            tools_log.append({"tool": "get_time", "args": {}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Stats del sistema
        if any(kw in text_lower for kw in ["sistema", "cpu", "ram", "disco", "procesos", "servidor"]):
            result = self.call_tool("get_system_stats")
            tools_log.append({"tool": "get_system_stats", "args": {}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Correo
        if any(kw in text_lower for kw in ["correo", "correos", "email"]):
            core = self.core
            if core and hasattr(core, "email") and core.email and core.email._is_configured():
                # Enviar correo
                if any(kw in text_lower for kw in ["enviar", "manda", "envia", "escribe"]):
                    result = core.email.send_email_from_text(text)
                # Correos no leidos
                elif any(kw in text_lower for kw in ["no leidos", "sin leer", "nuevos"]):
                    result = core.email.get_unread_emails_formatted()
                # Leer/revisar correos
                elif any(kw in text_lower for kw in ["leer", "revisar", "ver", "mostrar"]):
                    result = core.email.get_emails_formatted()
                # Default: mostrar recientes
                else:
                    result = core.email.get_emails_formatted()
            else:
                result = "El correo no esta configurado."
            tools_log.append({"tool": "email", "args": {"text": text}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Default
        duration = (time.time() - start) * 1000
        return AgentResult(
            response="No pude determinar que accion de sistema necesitas. Podes ser mas especifico?",
            agent=self.name,
            duration_ms=duration,
        )
