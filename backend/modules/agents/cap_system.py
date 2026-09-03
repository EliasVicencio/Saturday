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
            "salud", "pasos", "calorias", "calorías", "corazon", "corazón",
            "ritmo cardiaco", "ejercicio", "distancia", "como estoy", "cómo estoy",
            "drive", "nube", "archivos", "guardar archivo", "buscar archivo", "descargar",
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

        # Salud - Google Fit con analisis LLM
        if any(kw in text_lower for kw in ["salud", "pasos", "calorias", "calorías", "corazon", "corazón", "ritmo cardiaco", "ejercicio", "distancia", "como estoy", "cómo estoy"]):
            core = self.core
            result = "No hay datos de salud disponibles."
            
            if core and hasattr(core, "health") and core.health:
                try:
                    # Obtener datos de hoy (auto-sync)
                    today_data = core.health.get_today()
                    
                    if not today_data.get("data"):
                        if today_data.get("connected"):
                            result = "Google Fit esta conectado pero no hay datos de actividad hoy. Es normal si aun no has caminado."
                        else:
                            result = "Google Fit no esta conectado. Conecta en Configuracion para ver tus datos de salud."
                    else:
                        # Analisis con LLM
                        data = today_data["data"]
                        analysis = today_data.get("analysis", {})
                        
                        health_context = f"""Datos de salud de Elias para hoy:
- Pasos: {data.get('steps', 0)} / {analysis.get('steps', {}).get('goal', 10000)} ({analysis.get('steps', {}).get('pct', 0)}%)
- Calorias: {data.get('calories', 0)} / {analysis.get('calories', {}).get('goal', 2000)} ({analysis.get('calories', {}).get('pct', 0)}%)
- Distancia: {data.get('distance_km', 0)} km / {analysis.get('distance_km', {}).get('goal', 8)} km ({analysis.get('distance_km', {}).get('pct', 0)}%)
- Ritmo cardiaco promedio: {data.get('heart_rate_avg', 'N/A')} bpm
"""
                        
                        prompt = f"""Eres Saturday, el asistente personal de Elias. Analiza estos datos de salud y responde de forma natural y conversacional, como un entrenador personal.

REGLAS:
- Habla de forma natural, no como un listado de datos
- Solo menciona lo relevante
- Da recomendaciones concretas y accionables
- Si algo esta bien, elogia
- Si algo falta, sugiere que hacer
- Ejemplo: "Hoy caminaste 8000 pasos, vas bien. Te faltan 2000 para tu meta. ¿Quieres que te recuerde caminar un poco mas?"

Datos de salud:
{health_context}"""
                        
                        if core.gemini:
                            result = core.gemini.chat(prompt)
                        else:
                            # Fallback sin LLM
                            steps = data.get('steps', 0)
                            calories = data.get('calories', 0)
                            distance = data.get('distance_km', 0)
                            result = f"Paso: {steps} | Calorias: {calories} | Distancia: {distance} km"
                        
                except Exception as ex:
                    result = f"Error obteniendo datos de salud: {str(ex)}"
            else:
                result = "El seguimiento de salud no esta configurado."
            
            tools_log.append({"tool": "health", "args": {"text": text}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Google Drive
        if any(kw in text_lower for kw in ["drive", "nube", "archivos", "guardar archivo", "buscar archivo", "descargar"]):
            core = self.core
            result = "Google Drive no esta conectado."
            
            if core and hasattr(core, "google_drive") and core.google_drive:
                if core.google_drive.is_connected():
                    # List files
                    if any(kw in text_lower for kw in ["que tengo", "que hay", "listar", "mostrar", "ver archivos", "archivos"]):
                        files = core.google_drive.list_files(max_results=10)
                        if files:
                            lines = [f"Archivos en tu Drive ({len(files)}):"]
                            for f in files[:10]:
                                lines.append(f"  - {f.get('name', 'Sin nombre')}")
                            result = "\n".join(lines)
                        else:
                            result = "No hay archivos en tu Drive."
                    
                    # Search files
                    elif any(kw in text_lower for kw in ["buscar", "search", "encontrar"]):
                        query = text.replace("buscar", "").replace("search", "").replace("encontrar", "").strip()
                        if query:
                            files = core.google_drive.search_files(query)
                            if files:
                                lines = [f"Resultados para '{query}' ({len(files)}):"]
                                for f in files[:5]:
                                    lines.append(f"  - {f.get('name', 'Sin nombre')}")
                                result = "\n".join(lines)
                            else:
                                result = f"No encontre archivos con '{query}'."
                        else:
                            result = "¿Que archivo quieres buscar?"
                    
                    # Storage info
                    elif any(kw in text_lower for kw in ["espacio", "storage", "cuanto tengo", "cuanto espacio"]):
                        info = core.google_drive.get_storage_info()
                        if info:
                            result = f"Espacio: {info.get('used_gb', 0)} GB / {info.get('limit_gb', 0)} GB"
                        else:
                            result = "No pude obtener info de espacio."
                    
                    # Create file
                    elif any(kw in text_lower for kw in ["crear", "guardar", "save", "crear archivo"]):
                        content = text.replace("crear", "").replace("guardar", "").replace("save", "").replace("crear archivo", "").strip()
                        if content:
                            name = f"saturday_nota_{__import__('datetime').datetime.now().strftime('%Y-%m-%d_%H%M')}.md"
                            result_file = core.google_drive.create_file(name, content)
                            if result_file:
                                result = f"Archivo creado: {name}"
                            else:
                                result = "No pude crear el archivo."
                        else:
                            result = "¿Que contenido quieres guardar?"
                    
                    else:
                        info = core.google_drive.get_storage_info()
                        result = f"Google Drive conectado. Espacio: {info.get('used_gb', 0)} GB / {info.get('limit_gb', 0)} GB"
                else:
                    result = "Google Drive no esta conectado. Conecta en Configuracion."
            else:
                result = "Google Drive no esta configurado."
            
            tools_log.append({"tool": "google_drive", "args": {"text": text}})
            duration = (time.time() - start) * 1000
            return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

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
                result = "Abriendo el correo en Gmail..."
                tools_log.append({"tool": "open_email", "url": url, "args": {"url": url}})
                duration = (time.time() - start) * 1000
                return AgentResult(response=result, agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Default
        duration = (time.time() - start) * 1000
        return AgentResult(
            response="No pude determinar que accion de sistema necesitas. Podes ser mas especifico?",
            agent=self.name,
            duration_ms=duration,
        )
