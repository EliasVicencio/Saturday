# api/vault.py - Vault/Notes/Graph Blueprint
from flask import Blueprint, request, jsonify
from api.auth import require_api_key
import logging

logger = logging.getLogger("saturday.vault")

vault_bp = Blueprint("vault", __name__)

_saturday = None


def init_vault(saturday):
    global _saturday
    _saturday = saturday


@vault_bp.route("/api/vault/stats", methods=["GET"])
@require_api_key
def vault_stats():
    if not _saturday or not _saturday.vault:
        return jsonify({"error": "VaultManager no disponible"}), 500
    return jsonify(_saturday.vault.get_stats())


@vault_bp.route("/api/vault/notes", methods=["GET"])
@require_api_key
def vault_notes():
    from modules.input_validator import validate_vault_layer

    layer = request.args.get("layer", "wiki")
    valid, err = validate_vault_layer(layer)
    if not valid:
        return jsonify({"error": err}), 400
    if not _saturday or not _saturday.vault:
        return jsonify({"error": "VaultManager no disponible"}), 500
    return jsonify({"layer": layer, "notes": _saturday.vault.list_notes(layer)})


@vault_bp.route("/api/vault/note", methods=["GET"])
@require_api_key
def vault_note():
    query = request.args.get("q", "")
    result = _saturday.buscar_en_boveda(text=query)
    return jsonify({"result": result})


@vault_bp.route("/api/vault/note", methods=["POST"])
@require_api_key
def vault_create_note():
    from modules.input_validator import validate_note_input

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    content = data.get("content", data.get("text", "")).strip()
    valid, error = validate_note_input({"title": title, "content": content})
    if not valid:
        return jsonify({"error": error}), 400
    text = title + "\n\n" + content if title else content
    result = _saturday.guardar_en_boveda(text=text)
    return jsonify({"status": "saved", "result": result})


@vault_bp.route("/api/vault/search", methods=["GET"])
@require_api_key
def vault_search():
    query = request.args.get("q", "")
    result = _saturday.buscar_en_boveda(text=query)
    return jsonify({"results": result})


@vault_bp.route("/api/vault/graph", methods=["GET"])
@require_api_key
def vault_graph():
    if not _saturday or not _saturday.vault:
        return jsonify({"nodes": [], "edges": []})
    return jsonify(_saturday.vault.get_graph_json())
