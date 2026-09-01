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

        # Correo - Gmail con analisis LLM
        if any(kw in text_lower for kw in ["correo", "correos", "email", "gmail"]):
            core = self.core
            result = "No hay correos disponibles."
            
            # Resumen inteligente con LLM
            if any(kw in text_lower for kw in ["resumen", "analizar", "analiza", "revisar", "revise", "leer", "que hay", "actualizaciones"]):
                if core and hasattr(core, "email_summary") and core.email_summary:
                    try:
                        summary_data = core.email_summary.get_summary()
                        result = summary_data.get("summary", "No pude generar el resumen.")
                        emails = summary_data.get("emails", [])
                        if emails and len(emails) > 0:
                            result += f"\n\n{len(emails)} correo(s) analizado(s)."
                    except Exception as ex:
                        result = f"Error al resumir correos: {str(ex)}"
                else:
                    result = "El resumen de correos no esta configurado."
            
            # Enviar correo
            elif any(kw in text_lower for kw in ["enviar", "manda", "envia", "escribe"]):
                if core and hasattr(core, "email") and core.email and core.email._is_configured():
                    result = core.email.send_email_from_text(text)
                else:
                    result = "El envio de correos no esta configurado."
            
            # Gmail no leidos (raw)
            elif any(kw in text_lower for kw in ["no leidos", "sin leer", "nuevos", "raw", "bruto"]):
                if core and hasattr(core, "gmail") and core.gmail and core.gmail.is_connected():
                    emails = core.gmail.get_recent_emails(max_results=10)
                    if emails:
                        lines = []
                        for e in emails[:10]:
                            lines.append(f"De: {e.get('from','?')} | Asunto: {e.get('subject','Sin asunto')}")
                        result = f"{len(emails)} correos:\n" + "\n".join(lines)
                    else:
                        result = "No hay correos no leidos."
                else:
                    result = "Gmail no esta conectado. Conecta en Configuracion."
            
            # Default: resumen inteligente
            else:
                if core and hasattr(core, "email_summary") and core.email_summary:
                    try:
                        summary_data = core.email_summary.get_summary()
                        result = summary_data.get("summary", "No pude generar el resumen.")
                    except Exception:
                        result = "Error al obtener correos."
                elif core and hasattr(core, "gmail") and core.gmail and core.gmail.is_connected():
                    emails = core.gmail.get_recent_emails(max_results=5)
                    if emails:
                        lines = []
                        for e in emails[:5]:
                            lines.append(f"De: {e.get('from','?')} | Asunto: {e.get('subject','Sin asunto')}")
                        result = f"{len(emails)} correos recientes:\n" + "\n".join(lines)
                    else:
                        result = "No hay correos recientes."
                else:
                    result = "Gmail no esta conectado."
            
            tools_log.append({"tool": "email", "args": {"text": text}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Abrir correo pendiente
        if any(kw in text_lower for kw in ["si", "sí", "dale", "abre", "abrir", "claro", "por favor", "ok"]):
            core = self.core
            if core and hasattr(core, 'pending_email_url') and core.pending_email_url:
                url = core.pending_email_url
                core.pending_email_url = None
                result = f"Abrir correo en Gmail: {url}"
                tools_log.append({"tool": "open_email", "args": {"url": url}})
                duration = (time.time() - start) * 1000
                return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Default
        duration = (time.time() - start) * 1000
        return AgentResult(
            response="No pude determinar que accion de sistema necesitas. Podes ser mas especifico?",
            agent=self.name,
            duration_ms=duration,
        )
