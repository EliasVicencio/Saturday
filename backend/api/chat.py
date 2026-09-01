# api/chat.py - Chat & Conversation Blueprint
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger('saturday.chat')

chat_bp = Blueprint('chat', __name__)

_saturday = None
_sessions = {}

def init_chat(saturday, sessions):
    global _saturday, _sessions
    _saturday = saturday
    _sessions = sessions

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    from modules.input_validator import validate_message
    data = request.get_json(silent=True) or {}
    text = data.get('message', data.get('text', '')).strip()
    session_id = data.get('session_id', 'default')

    valid, error = validate_message(text)
    if not valid:
        return jsonify({'error': error}), 400

    result = _saturday.process_via_router(text, session_id=session_id)

    # Enrich with proactive context
    try:
        if _saturday.proactive:
            _saturday.proactive.record_interaction(result.get("intent", "unknown"), result.get("response", ""))
        if _saturday.routines:
            _saturday.routines.record_interaction(result.get("intent", "unknown"))
        if _saturday.productivity:
            _saturday.productivity.record_interaction(result.get("intent", "unknown"))
    except Exception:
        pass

    return jsonify(result)

@chat_bp.route('/api/greeting', methods=['GET'])
def greeting():
    if not _saturday:
        return jsonify({"response": "Hola! Soy Saturday."}), 200

    base = _saturday.get_greeting()
    response_data = {"response": base}

    # Add proactive suggestions to greeting
    try:
        if _saturday.proactive:
            ctx = _saturday.proactive.get_context()
            if ctx.get("suggestions"):
                suggestions_text = " | ".join([s["text"] for s in ctx["suggestions"][:2]])
                response_data["proactive_hint"] = suggestions_text
    except Exception:
        pass

    return jsonify(response_data)

@chat_bp.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    msgs = _sessions.get(session_id, [])
    return jsonify({'session_id': session_id, 'messages': msgs})