# api/chat.py - Chat & Conversation Blueprint
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger('saturday.chat')

chat_bp = Blueprint('chat', __name__)

# Will be set by app.py
_saturday = None
_sessions = {}

def init_chat(saturday, sessions):
    global _saturday, _sessions
    _saturday = saturday
    _sessions = sessions

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    from api.auth import require_api_key
    from modules.input_validator import validate_message
    data = request.get_json(silent=True) or {}
    text = data.get('message', data.get('text', '')).strip()
    session_id = data.get('session_id', 'default')

    valid, error = validate_message(text)
    if not valid:
        return jsonify({'error': error}), 400

    result = _saturday.process_via_router(text, session_id=session_id)
    return jsonify(result)

@chat_bp.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    from api.auth import require_api_key
    msgs = _sessions.get(session_id, [])
    return jsonify({'session_id': session_id, 'messages': msgs})
