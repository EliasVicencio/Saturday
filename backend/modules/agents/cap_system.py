# agents/cap_system.py - Agente de sistema: comandos SO, archivos, procesos
from .base import BaseAgent, AgentResult


class SystemAgent(BaseAgent):
    name = "system"
    description = "Control del sistema, archivos, procesos, configuracion"
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
        ]
        score = 0.0
        for kw in keywords:
            if kw in text_lower:
                score = max(score, 0.85)
                break
        return score

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = __import__("time").time()
        tools_log = []

        text_lower = text.lower()

        # Hora / fecha
        if any(kw in text_lower for kw in ["hora", "que hora es", "hora exacta"]):
            result = self.call_tool("get_time")
            tools_log.append({"tool": "get_time", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        if any(kw in text_lower for kw in ["fecha", "que fecha es", "que dia es"]):
            result = self.call_tool("get_time")
            tools_log.append({"tool": "get_time", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Stats del sistema
        if any(kw in text_lower for kw in ["sistema", "cpu", "ram", "disco", "procesos", "servidor"]):
            result = self.call_tool("get_system_stats")
            tools_log.append({"tool": "get_system_stats", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Default
        duration = (__import__("time").time() - start) * 1000
        return AgentResult(
            response="No pude determinar qué acción de sistema necesitás. ¿Podés ser más específico?",
            agent=self.name,
            duration_ms=duration,
        )
