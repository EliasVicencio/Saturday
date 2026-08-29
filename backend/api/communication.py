# api/communication.py - WhatsApp/Summary/Scheduler Blueprint
from flask import Blueprint, request, jsonify
import logging
import threading

logger = logging.getLogger("saturday.communication")

communication_bp = Blueprint("communication", __name__)

_saturday = None

def init_communication(saturday):
    global _saturday
    _saturday = saturday

@communication_bp.route("/api/whatsapp", methods=["POST"])
def send_whatsapp():
    from api.auth import require_api_key
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text"}), 400
    result = _saturday.send_whatsapp(text=text)
    return jsonify({"status": "sent" if result else "failed"})

@communication_bp.route("/api/whatsapp/voice", methods=["POST"])
def send_whatsapp_voice():
    from api.auth import require_api_key
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text"}), 400
    result = _saturday.send_whatsapp_voice(text=text)
    return jsonify({"status": "sent" if result else "failed"})

@communication_bp.route("/api/summary", methods=["POST"])
def send_summary():
    from api.auth import require_api_key
    _saturday.send_daily_summary()
    return jsonify({"status": "sent"})

@communication_bp.route("/api/scheduler/start", methods=["POST"])
def start_scheduler():
    from api.auth import require_api_key
    if _saturday.scheduler:
        _saturday.scheduler.start()
        return jsonify({"status": "started"})
    return jsonify({"error": "Scheduler not available"}), 503

@communication_bp.route("/api/scheduler/stop", methods=["POST"])
def stop_scheduler():
    from api.auth import require_api_key
    if _saturday.scheduler:
        _saturday.scheduler.stop()
        return jsonify({"status": "stopped"})
    return jsonify({"error": "Scheduler not available"}), 503
