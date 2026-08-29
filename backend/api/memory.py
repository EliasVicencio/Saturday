# api/memory.py - Memory CRUD Blueprint
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger('saturday.memory')

memory_bp = Blueprint('memory', __name__)

_saturday = None

def init_memory(saturday):
    global _saturday
    _saturday = saturday

@memory_bp.route('/api/memory', methods=['GET'])
def memory_list():
    from api.auth import require_api_key
    memories = _saturday.data.list_memories() if _saturday.data else []
    return jsonify({'memories': memories})

@memory_bp.route('/api/memory', methods=['POST'])
def memory_save():
    from api.auth import require_api_key
    from modules.input_validator import validate_text
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    valid, sanitized, error = validate_text(text)
    if not valid:
        return jsonify({'error': error}), 400
    memory_id = _saturday.data.save_memory(sanitized) if _saturday.data else None
    return jsonify({'id': memory_id, 'status': 'saved'})

@memory_bp.route('/api/memory/<int:memory_id>', methods=['GET'])
def memory_get(memory_id):
    from api.auth import require_api_key
    memory = _saturday.data.get_memory(memory_id) if _saturday.data else None
    if not memory:
        return jsonify({'error': 'Memory not found'}), 404
    return jsonify(memory)

@memory_bp.route('/api/memory/<int:memory_id>', methods=['PUT'])
def memory_update(memory_id):
    from api.auth import require_api_key
    from modules.input_validator import validate_text
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    valid, sanitized, error = validate_text(text)
    if not valid:
        return jsonify({'error': error}), 400
    _saturday.data.update_memory(memory_id, sanitized)
    return jsonify({'status': 'updated'})

@memory_bp.route('/api/memory/<int:memory_id>', methods=['DELETE'])
def memory_delete(memory_id):
    from api.auth import require_api_key
    _saturday.data.delete_memory(memory_id)
    return jsonify({'status': 'deleted'})

@memory_bp.route('/api/memory/forget', methods=['POST'])
def memory_forget():
    from api.auth import require_api_key
    data = request.get_json(silent=True) or {}
    query = data.get('query', '')
    _saturday.data.forget(query)
    return jsonify({'status': 'forgotten'})

@memory_bp.route('/api/memory/context/<session_id>', methods=['GET'])
def memory_context(session_id):
    from api.auth import require_api_key
    context = _saturday.data.get_context(session_id) if _saturday.data else ''
    return jsonify({'context': context})
