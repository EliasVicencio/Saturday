# backend/app.py - API para Saturday (refactored with Blueprints)
import sys
import os
import time
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("saturday")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.core import SaturdayCore

app = Flask(__name__)
CORS(app, origins=["https://saturday.viewdns.net", "http://localhost:5173"])
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per minute"])

API_KEY = os.getenv("SATURDAY_API_KEY", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", API_KEY + "-session")
SESSION_TTL = 3600

# Init auth module
from api.auth import auth_bp, init_auth, require_api_key, check_auth
init_auth(API_KEY, SESSION_SECRET, SESSION_TTL)
app.register_blueprint(auth_bp)

# Rutas que deben quedar públicas a propósito:
# - /api/health, /api/status: monitoreo externo (no exponen datos personales)
# - /api/auth/session: para poder pedir una sesión hay que dejar pasar la request
# - callbacks OAuth: Google redirige el navegador del usuario directo a estas URLs,
#   sin poder mandar el header X-API-Key, así que no se pueden proteger igual.
#   Cada callback valida su propio "state"/código de un solo uso internamente.
_PUBLIC_API_PATHS = {
    "/api/health",
    "/api/status",
    "/api/auth/session",
    "/api/health/google-fit/callback",
    "/api/gmail/callback",
    "/api/google-drive/callback",
}

@app.before_request
def _global_api_auth_guard():
    path = request.path
    if not path.startswith("/api/"):
        return  # frontend estático u otras rutas no-API
    if path in _PUBLIC_API_PATHS:
        return
    if not check_auth():
        logger.warning("Acceso no autorizado a %s desde %s", path, request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401

# Init Saturday Core
logger.info("=" * 50)
logger.info("SATURDAY - Backend API")
logger.info("=" * 50)
_start_time = time.time()
saturday = SaturdayCore()
logger.info("Saturday Core inicializado correctamente")

# Init all blueprints
from api.chat import chat_bp, init_chat
from api.memory import memory_bp, init_memory
from api.voice import voice_bp, init_voice
from api.calendar import calendar_bp, init_calendar
from api.communication import communication_bp, init_communication
from api.media import media_bp, init_media
from api.vault import vault_bp, init_vault
from api.vision import vision_bp, init_vision
from api.features import features_bp, init_features

_sessions = {}
init_chat(saturday, _sessions)
init_memory(saturday)
init_voice(saturday)
init_calendar(saturday)
init_communication(saturday)
init_media(saturday)
init_vault(saturday)
init_vision(saturday)
init_features(saturday)

app.register_blueprint(chat_bp)
app.register_blueprint(memory_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(communication_bp)
app.register_blueprint(media_bp)
app.register_blueprint(vault_bp)
app.register_blueprint(vision_bp)
app.register_blueprint(features_bp)

# Welcome message
_greeting_message = {"text": None, "ready": False}


def build_welcome_message(core):
    try:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos dias"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        clima_info = ""
        try:
            from modules.http_utils import get_with_retry

            api_key = os.getenv("WEATHER_API_KEY")
            city = os.getenv("SATURDAY_CITY", "Santiago")
            if api_key:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
                response = get_with_retry(url, timeout=5)
                if response and response.status_code == 200:
                    data = response.json()
                    temp = data["main"]["temp"]
                    desc = data["weather"][0]["description"]
                    clima_info = f" Hoy en {city} hace {temp}oC con {desc}."
        except (KeyError, TypeError):
            pass
        mensaje = f"{saludo}! Soy Saturday, tu asistente personal.{clima_info} Estoy listo para ayudarte."
        _greeting_message["text"] = mensaje
        _greeting_message["ready"] = True
    except Exception as e:
        logger.error("Error preparando saludo: %s", e)


saludo_thread = threading.Thread(target=build_welcome_message, args=(saturday,), daemon=True)
saludo_thread.start()


@app.route("/api/greeting", methods=["GET"])
def greeting():
    return jsonify({"ready": _greeting_message["ready"], "text": _greeting_message["text"]})


@app.route("/api/status", methods=["GET"])
def status():
    scheduler_running = False
    if saturday.scheduler:
        scheduler_running = saturday.scheduler.is_running
    return jsonify(
        {
            "status": "online",
            "version": "3.2.0",
            "modules": {
                "notion": saturday.notion is not None,
                "calendar": saturday.calendar is not None,
                "email": saturday.email is not None,
                "voice": saturday.voice is not None,
                "data": saturday.data is not None,
                "telegram": saturday.telegram is not None,
                "communication": saturday.communication is not None,
                "scheduler": scheduler_running,
            },
        }
    )


@app.route("/api/config", methods=["GET"])
@require_api_key
def config_get():
    from modules.config import config

    return jsonify({"config": config.to_dict()})


@app.route("/api/audit", methods=["GET"])
@require_api_key
def audit_log():
    from modules.security.audit import AuditLogger

    logs = AuditLogger().recent(limit=50)
    return jsonify({"logs": logs})


@app.route("/api/audit/stats", methods=["GET"])
@require_api_key
def audit_stats():
    from modules.security.audit import AuditLogger

    stats = AuditLogger().stats()
    return jsonify({"stats": stats})

@app.route("/api/autonomy", methods=["GET"])
def autonomy_status():
    """Estado actual de la autonomía: kill switch, niveles por acción y consumo del tope diario."""
    if not saturday.autonomy:
        return jsonify({"error": "AutonomyManager no disponible"}), 503
    return jsonify(saturday.autonomy.status())

@app.route("/api/autonomy/pause", methods=["POST"])
def autonomy_pause():
    """Kill switch: detiene TODA acción autónoma de inmediato, sin tocar el scheduler ni reiniciar el servicio."""
    if not saturday.autonomy:
        return jsonify({"error": "AutonomyManager no disponible"}), 503
    saturday.autonomy.pause()
    return jsonify({"status": "paused"})

@app.route("/api/autonomy/resume", methods=["POST"])
def autonomy_resume():
    if not saturday.autonomy:
        return jsonify({"error": "AutonomyManager no disponible"}), 503
    saturday.autonomy.resume()
    return jsonify({"status": "resumed"})

@app.route("/api/autonomy/level", methods=["POST"])
def autonomy_set_level():
    """Body: {"action": "email_check", "level": "auto" | "ask" | "never"}"""
    if not saturday.autonomy:
        return jsonify({"error": "AutonomyManager no disponible"}), 503
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    level = data.get("level", "")
    if not action:
        return jsonify({"error": "action es requerido"}), 400
    try:
        saturday.autonomy.set_level(action, level)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"status": "updated", "action": action, "level": level})

@app.route("/api/autonomy/trigger/<action>", methods=["POST"])
def autonomy_trigger(action):
    """Dispara a mano una tarea autónoma del scheduler, para poder probarla
    sin esperar al horario programado. Respeta los mismos permisos/kill
    switch que la versión automática - si algo está en 'ask' o 'never',
    o el kill switch está activo, esto tampoco la va a ejecutar."""
    if not saturday.scheduler:
        return jsonify({"error": "Scheduler no disponible"}), 503
    actions = {
        "email_check": saturday.scheduler.check_emails_autonomously,
        "news_check": saturday.scheduler.collect_news_autonomously,
        "morning_briefing": saturday.scheduler.send_morning_briefing,
        "data_organize": saturday.scheduler.organize_data_autonomously,
    }
    if action == "routine_suggestion":
        data = request.get_json(silent=True) or {}
        intent = data.get("intent", "revisar tu agenda")
        try:
            saturday.scheduler._suggest_from_routine(intent)
            return jsonify({"status": "ejecutado", "action": action, "intent": intent})
        except Exception as e:
            logger.error("Error disparando sugerencia de rutina manual: %s", e)
            return jsonify({"error": str(e)}), 500
    fn = actions.get(action)
    if not fn:
        return jsonify({"error": f"Acción desconocida. Opciones: {list(actions.keys())}"}), 400
    try:
        fn()
        return jsonify({"status": "ejecutado", "action": action})
    except Exception as e:
        logger.error("Error disparando acción manual '%s': %s", action, e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/permissions", methods=["GET"])
@require_api_key
def permissions_list():
    from modules.security.permissions import PermissionManager

    perms = PermissionManager().list_all()
    return jsonify({"permissions": {k: list(v) for k, v in perms.items()}})


@app.route("/api/permissions", methods=["POST"])
@require_api_key
def permissions_set():
    from modules.security.permissions import PermissionManager

    data = request.get_json(silent=True) or {}
    resource = data.get("resource", "")
    level = data.get("level", "private")
    pm = PermissionManager()
    if level == "revoked":
        pm.revoke(resource, "access")
    else:
        pm.grant(resource, "access")
    return jsonify({"status": "updated"})


# Privacy routes moved to api/vision.py blueprint


@app.route("/api/agents", methods=["GET"])
@require_api_key
def agents_list():
    agents = saturday.agent_router.list_agents() if saturday.agent_router else []
    return jsonify({"agents": agents})


@app.route("/api/agents/stats", methods=["GET"])
@require_api_key
def agents_stats():
    stats = saturday.agent_router.get_stats() if saturday.agent_router else {}
    return jsonify({"stats": stats})


@app.route("/api/agents/checkpoints", methods=["GET"])
@require_api_key
def agents_checkpoints():
    checkpoints = saturday.agent_router.get_checkpoints() if saturday.agent_router else []
    return jsonify({"checkpoints": checkpoints})


@app.route("/api/agents/confirm", methods=["POST"])
@require_api_key
def agents_confirm():
    data = request.get_json(silent=True) or {}
    checkpoint_id = data.get("checkpoint_id")
    approved = data.get("approved", True)
    saturday.agent_router.confirm_checkpoint(checkpoint_id, approved)
    return jsonify({"status": "confirmed"})


@app.route("/api/agents/pending", methods=["GET"])
@require_api_key
def agents_pending():
    pending = saturday.agent_router.get_pending() if saturday.agent_router else []
    return jsonify({"pending": pending})


@app.route("/api/agents/route", methods=["POST"])
@require_api_key
def agents_route():
    from modules.input_validator import validate_message

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    valid, error = validate_message(text)
    if not valid:
        return jsonify({"error": error}), 400
    result = saturday.process_via_router(text)
    return jsonify(result)


@app.route("/api/events/log", methods=["GET"])
@require_api_key
def events_list():
    events = saturday.event_bus.recent(limit=20) if saturday.event_bus else []
    return jsonify({"events": [e.to_dict() for e in events]})


@app.route("/api/events", methods=["POST"])
@require_api_key
def events_publish():
    data = request.get_json(silent=True) or {}
    event_name = data.get("name", "")
    event_data = data.get("data", {})
    if not event_name:
        return jsonify({"error": "name es requerido"}), 400
    saturday.event_bus.publish(event_name, event_data, source="api")
    return jsonify({"published": True, "event": event_name})


@app.route("/api/system", methods=["GET"])
@require_api_key
def system_stats():
    import psutil

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime = time.time() - _start_time
    return jsonify(
        {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_percent": disk,
            "uptime_seconds": int(uptime),
        }
    )


@app.route("/api/health", methods=["GET"])
def health():
    import psutil

    return jsonify(
        {
            "status": "ok",
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "uptime_seconds": int(time.time() - _start_time),
            "version": "3.2.0",
            "modules": {
                "calendar": saturday.calendar is not None,
                "conversation": saturday.conversation is not None,
                "notion": saturday.notion is not None,
                "voice": saturday.voice is not None,
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
