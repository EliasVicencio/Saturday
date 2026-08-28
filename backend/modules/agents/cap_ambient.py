# agents/cap_ambient.py - Agente ambiental: vision, camaras, sensores, presencia
from .base import BaseAgent, AgentResult


class AmbientAgent(BaseAgent):
    name = "ambient"
    description = "Vision, camaras, sensores, privacidad, presencia"
    tools = ["describe_scene", "privacy_status"]

    def can_handle(self, text: str) -> float:
        text_lower = text.lower()
        keywords = {
            "camara": 0.9, "camaras": 0.9, "ver": 0.5, "mirar": 0.5,
            "que hay": 0.7, "que ves": 0.8, "describe": 0.6,
            "vision": 0.9, "imagen": 0.8, "foto": 0.8, "captura": 0.8,
            "privacidad": 0.95, "permisos": 0.8, "sensores": 0.9,
            "kill": 0.7, "apagar todo": 0.9, "restaurar": 0.8,
            "microfono": 0.8, "ubicacion": 0.8, "camara del celular": 0.9,
            "dispositivo": 0.6,
        }
        score = 0.0
        for kw, s in keywords.items():
            if kw in text_lower:
                score = max(score, s)
        return score

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = __import__("time").time()
        tools_log = []
        text_lower = text.lower()

        # Kill all / Apagar todo
        if any(kw in text_lower for kw in ["kill all", "apagar todo", "desactivar todo"]):
            if self.core and self.core.privacy:
                result = self.core.privacy.kill_all()
                tools_log.append({"tool": "privacy_kill_all", "args": {}})
                if self.core.event_bus:
                    self.core.event_bus.publish("privacy.kill_all", {"killed": result}, source="agent")
                duration = (__import__("time").time() - start) * 1000
                return AgentResult(
                    response=f"Desactivados {result} sensores/permisos. Todo apagado por privacidad.",
                    agent=self.name, tools_called=tools_log, duration_ms=duration,
                )

        # Restaurar todo
        if any(kw in text_lower for kw in ["restaurar", "restaurar todo", "activar todo"]):
            if self.core and self.core.privacy:
                result = self.core.privacy.restore_all()
                tools_log.append({"tool": "privacy_restore_all", "args": {}})
                duration = (__import__("time").time() - start) * 1000
                return AgentResult(
                    response=f"Restaurados {result} sensores/permisos.",
                    agent=self.name, tools_called=tools_log, duration_ms=duration,
                )

        # Privacidad status
        if any(kw in text_lower for kw in ["privacidad", "permisos", "sensores"]):
            result = self.call_tool("privacy_status")
            tools_log.append({"tool": "privacy_status", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Vision / Camara
        if any(kw in text_lower for kw in ["camara", "camaras", "ver", "mirar", "que hay", "que ves", "describe", "vision", "imagen", "foto", "captura"]):
            question = "Que hay en la imagen?"
            if "?" in text:
                question = text.split("?")[0].strip()
                if any(kw in question.lower() for kw in ["que", "como", "donde", "cuantos"]):
                    question = question
                else:
                    question = "Que hay: " + question
            result = self.call_tool("describe_scene", {"question": question})
            tools_log.append({"tool": "describe_scene", "args": {"question": question}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        duration = (__import__("time").time() - start) * 1000
        return AgentResult(response="No pude interpretar qué acción ambiental necesitás.", agent=self.name, duration_ms=duration)
