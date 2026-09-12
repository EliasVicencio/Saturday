# api/calendar.py - Calendar/Tasks/Events/Notes Blueprint
from flask import Blueprint, request, jsonify
from api.auth import require_api_key
import logging

logger = logging.getLogger("saturday.calendar")

calendar_bp = Blueprint("calendar", __name__)

_saturday = None


def init_calendar(saturday):
    global _saturday
    _saturday = saturday


@calendar_bp.route("/api/tasks", methods=["GET"])
@require_api_key
def get_tasks():
    if not _saturday or not _saturday.notion:
        return jsonify({"tasks": []})
    try:
        tasks = _saturday.notion.get_tasks(status="Todo", limit=8)
        return jsonify({"tasks": [{"title": t.get("name", "Sin titulo")} for t in tasks]})
    except Exception as e:
        logger.error("Error obteniendo tareas: %s", e)
        return jsonify({"tasks": []})


@calendar_bp.route("/api/tasks/list", methods=["GET"])
@require_api_key
def get_tasks_list():
    if not _saturday or not _saturday.notion:
        return jsonify({"tasks": []})
    try:
        tasks = _saturday.notion.get_tasks(status="Todo", limit=8)
        return jsonify({"tasks": [{"title": t.get("name", "Sin titulo")} for t in tasks]})
    except Exception as e:
        logger.error("Error obteniendo tareas: %s", e)
        return jsonify({"tasks": []})


@calendar_bp.route("/api/events", methods=["GET"])
@require_api_key
def get_events():
    limit = request.args.get("limit", 20, type=int)
    if _saturday and _saturday.event_bus:
        events = _saturday.event_bus.recent(limit=limit)
        return jsonify({"events": [e.to_dict() for e in events]})
    return jsonify({"events": []})


@calendar_bp.route("/api/events/today", methods=["GET"])
@require_api_key
def get_events_today():
    if not _saturday or not _saturday.calendar:
        return jsonify({"events": []})
    try:
        events = _saturday.calendar.get_events_today_list()
        return jsonify({"events": events})
    except Exception as e:
        logger.error("Error obteniendo eventos: %s", e)
        return jsonify({"events": []})


@calendar_bp.route("/api/notes", methods=["GET"])
@require_api_key
def get_notes():
    notes = _saturday.get_notes()
    return jsonify({"notes": notes})


@calendar_bp.route("/api/camera", methods=["GET"])
@require_api_key
def camera():
    result = _saturday.get_camera()
    return jsonify({"image": result})
