# api/calendar.py - Calendar/Tasks/Events/Notes Blueprint
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger('saturday.calendar')

calendar_bp = Blueprint('calendar', __name__)

_saturday = None

def init_calendar(saturday):
    global _saturday
    _saturday = saturday

@calendar_bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    from api.auth import require_api_key
    tasks = _saturday.get_tasks()
    return jsonify({'tasks': tasks})

@calendar_bp.route('/api/tasks/list', methods=['GET'])
def get_tasks_list():
    from api.auth import require_api_key
    tasks = _saturday.get_tasks()
    return jsonify({'tasks': tasks})

@calendar_bp.route('/api/events', methods=['GET'])
def get_events():
    from api.auth import require_api_key
    events = _saturday.get_events()
    return jsonify({'events': events})

@calendar_bp.route('/api/events/today', methods=['GET'])
def get_events_today():
    from api.auth import require_api_key
    events = _saturday.get_events_today()
    return jsonify({'events': events})

@calendar_bp.route('/api/notes', methods=['GET'])
def get_notes():
    from api.auth import require_api_key
    notes = _saturday.get_notes()
    return jsonify({'notes': notes})

@calendar_bp.route('/api/camera', methods=['GET'])
def camera():
    from api.auth import require_api_key
    result = _saturday.get_camera()
    return jsonify({'image': result})
