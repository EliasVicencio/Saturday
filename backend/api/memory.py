# api/memory.py - Memory CRUD Blueprint
from flask import Blueprint, request, jsonify
import logging
import hashlib

logger = logging.getLogger('saturday.memory')

memory_bp = Blueprint('memory', __name__)

_saturday = None

def init_memory(saturday):
    global _saturday
    _saturday = saturday

@memory_bp.route('/api/memory', methods=['GET'])
def memory_list():
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    mem_type = request.args.get('type', '')
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 20) or 20), 100)
    if query:
        results = _saturday.memory_store.search(query=query, mem_type=mem_type, limit=limit)
    else:
        results = _saturday.memory_store.recent(limit=limit)
    return jsonify({'memories': [m.to_dict() for m in results], 'total': _saturday.memory_store.count()})

@memory_bp.route('/api/memory', methods=['POST'])
def memory_save():
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    data = request.json
    content_val = data.get('content', '').strip()
    if not content_val:
        return jsonify({'error': 'content es requerido'}), 400
    session_id = data.get('session_id', '')
    chat_id = None
    if session_id:
        chat_id = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % (10**9)
    mid = _saturday.memory_store.save(
        mem_type=data.get('type', 'note'),
        content=content_val,
        source=data.get('source', 'manual'),
        confidence=float(data.get('confidence', 1.0) or 1.0),
        chat_id=chat_id,
        tags=data.get('tags', ''),
    )
    return jsonify({'id': mid, 'saved': True})

@memory_bp.route('/api/memory/<int:memory_id>', methods=['GET'])
def memory_get(memory_id):
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    mem = _saturday.memory_store.get(memory_id)
    if not mem:
        return jsonify({'error': 'Recuerdo no encontrado'}), 404
    return jsonify(mem.to_dict())

@memory_bp.route('/api/memory/<int:memory_id>', methods=['PUT'])
def memory_update(memory_id):
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    data = request.json
    updates = {}
    for key in ('content', 'type', 'confidence', 'tags', 'source'):
        if key in data:
            updates['mem_type' if key == 'type' else key] = data[key]
    ok = _saturday.memory_store.update(memory_id, **updates)
    return jsonify({'updated': ok})

@memory_bp.route('/api/memory/<int:memory_id>', methods=['DELETE'])
def memory_delete(memory_id):
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    ok = _saturday.memory_store.delete(memory_id)
    return jsonify({'deleted': ok})

@memory_bp.route('/api/memory/forget', methods=['POST'])
def memory_forget():
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_store:
        return jsonify({'error': 'MemoryStore no disponible'}), 503
    data = request.json
    query = data.get('query', '')
    session_id = data.get('session_id', '')
    if session_id:
        chat_id = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % (10**9)
        count = _saturday.memory_store.delete_by_chat(chat_id)
        return jsonify({'deleted': count, 'scope': 'session'})
    return jsonify({'status': 'forgotten'})

@memory_bp.route('/api/memory/context/<session_id>', methods=['GET'])
def memory_context(session_id):
    from api.auth import require_api_key
    if not _saturday or not _saturday.memory_retriever:
        return jsonify({'error': 'MemoryRetriever no disponible'}), 503
    chat_id = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % (10**9)
    query = request.args.get('q', 'contexto general del usuario')
    context = _saturday.memory_retriever.before_respond(query, chat_id)
    facts = _saturday.memory_retriever.get_user_facts(chat_id)
    prefs = _saturday.memory_retriever.get_user_preferences(chat_id)
    return jsonify({'context': context, 'facts': [f.to_dict() for f in facts], 'preferences': [p.to_dict() for p in prefs]})
