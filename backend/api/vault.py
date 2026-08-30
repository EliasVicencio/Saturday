# api/vault.py - Vault/Notes/Graph Blueprint
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger("saturday.vault")

vault_bp = Blueprint("vault", __name__)

_saturday = None

def init_vault(saturday):
    global _saturday
    _saturday = saturday

@vault_bp.route("/api/vault/stats", methods=["GET"])
def vault_stats():
    from api.auth import require_api_key
    if not _saturday or not _saturday.vault:
        return jsonify({"error": "VaultManager no disponible"}), 500
    return jsonify(_saturday.vault.get_stats())

@vault_bp.route("/api/vault/notes", methods=["GET"])
def vault_notes():
    from api.auth import require_api_key
    from modules.input_validator import validate_vault_layer
    layer = request.args.get("layer", "wiki")
    valid, err = validate_vault_layer(layer)
    if not valid:
        return jsonify({"error": err}), 400
    if not _saturday or not _saturday.vault:
        return jsonify({"error": "VaultManager no disponible"}), 500
    return jsonify({"layer": layer, "notes": _saturday.vault.list_notes(layer)})

@vault_bp.route("/api/vault/note", methods=["GET"])
def vault_note():
    from api.auth import require_api_key
    query = request.args.get("q", "")
    result = _saturday.buscar_en_boveda(text=query)
    return jsonify({"result": result})

@vault_bp.route("/api/vault/note", methods=["POST"])
def vault_create_note():
    from api.auth import require_api_key
    from modules.input_validator import validate_note_input
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    valid, sanitized, error = validate_note_input(text)
    if not valid:
        return jsonify({"error": error}), 400
    result = _saturday.guardar_en_boveda(text=sanitized)
    return jsonify({"status": "saved", "result": result})

@vault_bp.route("/api/vault/search", methods=["GET"])
def vault_search():
    from api.auth import require_api_key
    query = request.args.get("q", "")
    result = _saturday.buscar_en_boveda(text=query)
    return jsonify({"results": result})

@vault_bp.route("/api/vault/graph", methods=["GET"])
def vault_graph():
    from api.auth import require_api_key
    if not _saturday or not _saturday.vault:
        return jsonify({"nodes": [], "edges": []})
    return jsonify(_saturday.vault.get_graph_json())
