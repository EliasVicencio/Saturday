# modules/scheduler.py
import schedule
import time
import threading
import logging
import hashlib
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger("saturday.scheduler")


class Scheduler:
    """Gestor de tareas programadas y autónomas de Saturday.

    Todas las tareas "autónomas" (las que Saturday ejecuta sin que el
    usuario pregunte) pasan por `AutonomyManager` (kill switch + niveles
    por acción) y, cuando es posible, por `AgentRouter` para que queden
    sujetas a las mismas reglas de permisos/checkpoints que una acción
    pedida directamente por el usuario.
    """

    def __init__(self, core):
        self.core = core
        self.jobs = []
        self.is_running = False
        self.thread = None
        self._last_email_digest: Optional[str] = None
        logger.info("Scheduler inicializado")

    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler iniciado en segundo plano")

    def _run(self):
        """Ejecuta el bucle del scheduler"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        """Detiene el scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Scheduler detenido")

    # ============ AUTONOMÍA: helpers ============

    def _autonomy(self):
        """Devuelve el AutonomyManager del core, o None si no existe."""
        return getattr(self.core, "autonomy", None)

    def _allowed(self, action: str) -> bool:
        """Chequea kill switch + nivel de autonomía antes de ejecutar algo solo."""
        autonomy = self._autonomy()
        if autonomy is None:
            logger.warning("AutonomyManager no disponible, se omite acción autónoma '%s'", action)
            return False
        if autonomy.paused:
            logger.info("Autonomía en pausa (kill switch). Se omite '%s'", action)
            return False
        if not autonomy.allows(action):
            logger.info("Acción '%s' requiere confirmación humana, no se ejecuta sola", action)
            return False
        return True

    def _route(self, text: str, session_id: str = "autonomous") -> Optional[dict]:
        """Ejecuta un mensaje a través del AgentRouter, igual que si lo hubiera
        escrito el usuario. Así toda acción autónoma queda auditada (checkpoints)
        y sujeta al sistema de permisos/confirmación existente."""
        if not self.core or not getattr(self.core, "agent_router", None):
            return None
        try:
            return self.core.agent_router.route(text, session_id=session_id)
        except Exception as e:
            logger.error("Error enrutando tarea autónoma '%s': %s", text, e)
            return None

    def send_daily_summary(self):
        """Envía el resumen diario"""
        if not self._allowed("daily_summary"):
            return
        logger.info("Enviando resumen diario programado (%s)", datetime.now())
        if self.core.daily_summary:
            result = self.core.daily_summary.send(via="whatsapp")
            if result.get('success'):
                logger.info("Resumen diario enviado")
            else:
                logger.error("Error enviando resumen: %s", result.get('error'))
        else:
            logger.warning("DailySummary no disponible")

    def schedule_daily_summary(self, hour: int = 8, minute: int = 0):
        """Programa el envío del resumen diario"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.send_daily_summary)
        self.jobs.append({'type': 'daily_summary', 'hour': hour, 'minute': minute})
        logger.info("Resumen diario programado para las %02d:%02d", hour, minute)

    # ============ TAREAS AUTÓNOMAS ============

    def check_emails_autonomously(self):
        """Revisa correos y guarda resumen en la bóveda. Es de solo lectura
        (no responde ni borra nada), por eso puede correr en modo 'auto'.

        Si encuentra correos nuevos (distintos a la última revisión), avisa
        por WhatsApp (punto 4: que se note cuando actuó solo) y, si detecta
        palabras clave de urgencia, encadena automáticamente una consulta de
        calendario a través del router para sugerir agendar algo (punto 5:
        encadenar pasos en vez de un solo tiro por mensaje)."""
        if not self._allowed("email_check"):
            return
        logger.info("Revisando correos automáticamente (%s)", datetime.now())
        if not self.core.email:
            logger.warning("Email no disponible")
            return
        try:
            emails = self.core.email.get_unread_emails_formatted()
            has_new = emails and "No tienes correos" not in emails and "No hay correos" not in emails
            if has_new:
                if self.core.vault:
                    self.core.vault.save_raw(
                        f"Correos no leídos ({datetime.now().strftime('%H:%M')}):\n{emails}",
                        source="autonomo"
                    )
                logger.info("Correos revisados y guardados")

                digest = hashlib.sha256(emails.encode("utf-8", "ignore")).hexdigest()
                if digest != self._last_email_digest:
                    self._last_email_digest = digest
                    self._notify_new_emails(emails)
            else:
                logger.info("No hay correos nuevos")
        except Exception as e:
            logger.error("Error revisando correos: %s", e)

    _URGENT_KEYWORDS = ("urgente", "reunión", "reunion", "factura", "pago", "vence", "hoy", "mañana", "manana")

    def _notify_new_emails(self, emails_text: str):
        """Avisa que hay correos nuevos, y si suenan urgentes, encadena una
        revisión de calendario a través del AgentRouter (no ejecuta nada
        destructivo, solo consulta y sugiere)."""
        preview = emails_text.strip().splitlines()[:3]
        preview_text = " / ".join(l.strip() for l in preview if l.strip())[:200]
        looks_urgent = any(kw in emails_text.lower() for kw in self._URGENT_KEYWORDS)

        if self._allowed("proactive_notify") and self.core.communication:
            try:
                msg = f"Te llegaron correos nuevos: {preview_text}"
                if looks_urgent:
                    msg += "\nAlgo ahí suena a que puede tener fecha/urgencia, reviso tu agenda."
                self.core.communication.send_whatsapp_message(msg)
            except Exception as e:
                logger.error("Error notificando correos nuevos: %s", e)

        if looks_urgent:
            # Paso encadenado: le pedimos al router que mire la agenda,
            # exactamente como si el usuario hubiera escrito el mensaje.
            result = self._route(
                "Revisa mi agenda de hoy y de mañana y dime si hay algo que se cruce con un correo urgente que acabo de recibir",
                session_id="autonomous-email-chain",
            )
            if result and self._allowed("proactive_notify") and self.core.communication:
                try:
                    self.core.communication.send_whatsapp_message(result.get("response", ""))
                except Exception as e:
                    logger.error("Error enviando resultado del chain de agenda: %s", e)

    def collect_news_autonomously(self):
        """Recolecta noticias del día y guarda en la bóveda (solo lectura)."""
        if not self._allowed("news_check"):
            return
        logger.info("Recolectando noticias automáticamente (%s)", datetime.now())
        if not self.core.news or not self.core.news.is_available():
            logger.warning("News no disponible")
            return
        try:
            articles = self.core.news.get_top_headlines(limit=5)
            if articles:
                news_text = "Noticias del día:\n"
                for i, article in enumerate(articles, 1):
                    news_text += f"{i}. {article.get('title', 'Sin título')}\n"
                if self.core.vault:
                    self.core.vault.save_raw(
                        f"Noticias ({datetime.now().strftime('%d/%m %H:%M')}):\n{news_text}",
                        source="autonomo"
                    )
                logger.info("%d noticias recolectadas", len(articles))
            else:
                logger.info("No se encontraron noticias")
        except Exception as e:
            logger.error("Error recolectando noticias: %s", e)

    def organize_data_autonomously(self):
        """Organiza y resume datos del día (solo lectura)."""
        if not self._allowed("data_organize"):
            return
        logger.info("Organizando datos del día (%s)", datetime.now())
        try:
            if self.core.data:
                stats = self.core.data.get_stats()
                logger.info("Estadísticas: %s", stats)
        except Exception as e:
            logger.error("Error organizando datos: %s", e)

    def send_morning_briefing(self):
        """Genera el briefing con ProactiveContext y lo envía por WhatsApp.
        Esta sí es una acción que 'sale hacia afuera' (manda un mensaje), así
        que por defecto su nivel de autonomía es 'ask' salvo que el usuario
        lo suba explícitamente a 'auto' desde /api/autonomy."""
        if not self._allowed("proactive_notify"):
            return
        if not getattr(self.core, "proactive", None):
            return
        try:
            ctx = self.core.proactive.get_context()
            text = f"Buenos días. {ctx.get('summary', '')}."
            for s in ctx.get("suggestions", []):
                text += f"\n- {s['text']}"
            if self.core.communication:
                self.core.communication.send_whatsapp_message(text)
                logger.info("Briefing matutino enviado")
        except Exception as e:
            logger.error("Error enviando briefing matutino: %s", e)

    def schedule_autonomous_tasks(self):
        """Programa todas las tareas autónomas de solo-lectura."""
        schedule.every(4).hours.do(self.check_emails_autonomously)
        logger.info("Revisión de correos programada (cada 4h)")

        schedule.every().day.at("08:00").do(self.collect_news_autonomously)
        logger.info("Recolectar noticias programada (08:00)")

        schedule.every().day.at("08:05").do(self.send_morning_briefing)
        logger.info("Briefing matutino programado (08:05)")

        schedule.every().day.at("20:00").do(self.organize_data_autonomously)
        logger.info("Organizar datos programada (20:00)")

    def schedule_from_routines(self):
        """Lee los patrones detectados por RoutineLearner y auto-programa
        una tarea de 'recordatorio suave' en los horarios donde el usuario
        pide algo de forma recurrente. No ejecuta acciones desconocidas por
        su cuenta: solo dispara una sugerencia, que respeta permisos/autonomía."""
        routines = getattr(self.core, "routines", None)
        if not routines:
            return
        data = routines.get_routines()
        if data.get("status") != "active":
            logger.info("RoutineLearner aún sin suficientes datos para auto-programar")
            return

        hourly = data.get("hourly_routines", {})
        scheduled = 0
        for hour_str, items in hourly.items():
            top = items[0] if items else None
            if not top or top.get("frequency", 0) < 3:
                continue
            hour = int(hour_str)
            intent = top["intent"]
            schedule.every().day.at(f"{hour:02d}:00").do(self._suggest_from_routine, intent)
            scheduled += 1

        self.jobs.append({'type': 'routine_based', 'count': scheduled})
        logger.info("%d recordatorios auto-programados desde rutinas aprendidas", scheduled)

    def _suggest_from_routine(self, intent: str):
        if not self._allowed("proactive_notify"):
            return
        logger.info("Rutina detectada a esta hora: '%s'", intent)
        if self.core.communication:
            try:
                self.core.communication.send_whatsapp_message(
                    f"A esta hora normalmente haces '{intent}'. ¿Quieres que lo haga ahora?"
                )
            except Exception as e:
                logger.error("Error enviando sugerencia de rutina: %s", e)

    def schedule_reminder(self, text: str, hour: int, minute: int):
        """Programa un recordatorio pedido explícitamente por el usuario."""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._send_reminder, text)
        logger.info("Recordatorio programado: '%s' a las %02d:%02d", text, hour, minute)

    def _send_reminder(self, text: str):
        # Los recordatorios pedidos explícitamente por el usuario no pasan por
        # el gate de autonomía: el usuario ya dio el consentimiento al crearlos.
        logger.info("Enviando recordatorio: %s", text)
        if self.core.communication:
            self.core.communication.send_whatsapp_message(f"RECORDATORIO: {text}")

    def list_jobs(self) -> list:
        """Lista las tareas programadas"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'next_run': str(job.next_run),
                'interval': str(job.interval),
                'unit': str(job.unit),
            })
        return jobs
