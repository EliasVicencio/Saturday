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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
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
from api.auth import auth_bp, init_auth
init_auth(API_KEY, SESSION_SECRET, SESSION_TTL)
app.register_blueprint(auth_bp)

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

_sessions = {}
init_chat(saturday, _sessions)
init_memory(saturday)
init_voice(saturday)
init_calendar(saturday)
init_communication(saturday)
init_media(saturday)
init_vault(saturday)

app.register_blueprint(chat_bp)
app.register_blueprint(memory_bp)
app.register_blueprint(voice_bp)
app.register_blueprint(calendar_bp)
app.register_blueprint(communication_bp)
app.register_blueprint(media_bp)
app.register_blueprint(vault_bp)

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
    return jsonify({
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
    })

@app.route("/api/config", methods=["GET"])
def config_get():
    from modules.config import config
    return jsonify({"config": config.to_dict()})

@app.route("/api/audit", methods=["GET"])
def audit_log():
    from modules.security.audit import get_audit_log
    logs = get_audit_log()
    return jsonify({"logs": logs})

@app.route("/api/audit/stats", methods=["GET"])
def audit_stats():
    from modules.security.audit import get_audit_stats
    stats = get_audit_stats()
    return jsonify({"stats": stats})

@app.route("/api/permissions", methods=["GET"])
def permissions_list():
    from modules.security.permissions import list_permissions
    perms = list_permissions()
    return jsonify({"permissions": perms})

@app.route("/api/permissions", methods=["POST"])
def permissions_set():
    from modules.security.permissions import set_permission
    data = request.get_json(silent=True) or {}
    set_permission(data.get("resource", ""), data.get("level", "private"))
    return jsonify({"status": "updated"})

@app.route("/api/privacy", methods=["GET"])
def privacy_get():
    return jsonify(saturday._privacy_status())

@app.route("/api/privacy", methods=["POST"])
def privacy_set():
    data = request.get_json(silent=True) or {}
    saturday.privacy_mode = data.get("privacy_mode", False)
    return jsonify({"privacy_mode": saturday.privacy_mode})

@app.route("/api/agents", methods=["GET"])
def agents_list():
    agents = saturday.router.list_agents() if saturday.router else []
    return jsonify({"agents": agents})

@app.route("/api/agents/stats", methods=["GET"])
def agents_stats():
    stats = saturday.router.get_stats() if saturday.router else {}
    return jsonify({"stats": stats})

@app.route("/api/agents/checkpoints", methods=["GET"])
def agents_checkpoints():
    checkpoints = saturday.router.get_checkpoints() if saturday.router else []
    return jsonify({"checkpoints": checkpoints})

@app.route("/api/agents/confirm", methods=["POST"])
def agents_confirm():
    data = request.get_json(silent=True) or {}
    checkpoint_id = data.get("checkpoint_id")
    approved = data.get("approved", True)
    saturday.router.confirm_checkpoint(checkpoint_id, approved)
    return jsonify({"status": "confirmed"})

@app.route("/api/agents/pending", methods=["GET"])
def agents_pending():
    pending = saturday.router.get_pending() if saturday.router else []
    return jsonify({"pending": pending})

@app.route("/api/agents/route", methods=["POST"])
def agents_route():
    from modules.input_validator import validate_message
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    valid, sanitized, error = validate_message(text)
    if not valid:
        return jsonify({"error": error}), 400
    result = saturday.process_via_router(sanitized)
    return jsonify(result)

@app.route("/api/events/log", methods=["GET"])
def events_list():
    events = saturday.event_bus.recent(limit=20) if saturday.event_bus else []
    return jsonify({"events": [e.to_dict() for e in events]})

@app.route("/api/events", methods=["POST"])
def events_publish():
    data = request.get_json(silent=True) or {}
    event_name = data.get("name", "")
    event_data = data.get("data", {})
    if not event_name:
        return jsonify({"error": "name es requerido"}), 400
    saturday.event_bus.publish(event_name, event_data, source="api")
    return jsonify({"published": True, "event": event_name})

@app.route("/api/system", methods=["GET"])
def system_stats():
    import psutil
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    uptime = time.time() - _start_time
    return jsonify({
        "cpu_percent": cpu,
        "ram_percent": ram,
        "disk_percent": disk,
        "uptime_seconds": int(uptime),
    })

@app.route("/api/health", methods=["GET"])
def health():
    import psutil
    return jsonify({
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
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
