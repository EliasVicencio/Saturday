# api/vision.py - Vision/Camera/Privacy Blueprint
from flask import Blueprint, request, jsonify
import os, tempfile, logging
from api.auth import require_api_key

logger = logging.getLogger("saturday.vision")

vision_bp = Blueprint("vision", __name__)

_saturday = None

def init_vision(saturday):
    global _saturday
    _saturday = saturday


@vision_bp.route("/api/vision/status", methods=["GET"])
@require_api_key
def vision_status():
    camera_status = _saturday.camera.get_status() if _saturday.camera else {"available": False}
    vision_available = _saturday.vision.is_available if _saturday.vision else False
    return jsonify({"camera": camera_status, "vision_model": vision_available})


@vision_bp.route("/api/vision/capture", methods=["POST"])
@require_api_key
def vision_capture():
    import base64 as b64mod
    if not _saturday.camera:
        return jsonify({"error": "CameraManager no disponible"}), 503
    if not _saturday.privacy or not _saturday.privacy.is_enabled("camera_enabled"):
        return jsonify({"error": "Camara desactivada por privacidad"}), 403
    data = request.json or {}
    question = data.get("question", "Que hay en esta imagen?")
    img_b64 = _saturday.camera.capture()
    if not img_b64:
        return jsonify({"error": "No se pudo capturar imagen"}), 500
    description = None
    if _saturday.vision and _saturday.vision.is_available:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b64mod.b64decode(img_b64))
            tmp_path = f.name
        try:
            description = _saturday.vision.describe(tmp_path, question)
        finally:
            os.unlink(tmp_path)
    if _saturday.event_bus:
        _saturday.event_bus.publish("vision.captured", {"description": description or "sin descripcion"}, source="api")
    return jsonify({
        "captured": True,
        "simulated": _saturday.camera.last_capture.get("simulated", True) if _saturday.camera.last_capture else True,
        "description": description,
        "timestamp": _saturday.camera.last_capture.get("timestamp") if _saturday.camera.last_capture else None,
    })


@vision_bp.route("/api/vision/capture-device", methods=["POST"])
@require_api_key
def vision_capture_device():
    import base64 as b64mod
    from datetime import datetime as dt
    data = request.json or {}
    image_b64 = data.get("image", "")
    question = data.get("question", "Que hay en esta imagen?")
    if not image_b64:
        return jsonify({"error": "image es requerido (base64)"}), 400
    if not _saturday.privacy or not _saturday.privacy.is_enabled("camera_enabled"):
        return jsonify({"error": "Camaras desactivadas por privacidad"}), 403
    description = None
    if _saturday.vision and _saturday.vision.is_available:
        img_bytes = b64mod.b64decode(image_b64)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(img_bytes)
            tmp_path = f.name
        try:
            description = _saturday.vision.describe(tmp_path, question)
        finally:
            os.unlink(tmp_path)
    if _saturday.event_bus:
        _saturday.event_bus.publish("vision.captured_device", {"description": description or "sin descripcion"}, source="device")
    return jsonify({
        "captured": True,
        "simulated": False,
        "description": description,
        "timestamp": dt.now().isoformat(),
    })


@vision_bp.route("/api/privacy", methods=["GET"])
@require_api_key
def privacy_get():
    if not _saturday or not _saturday.privacy:
        return jsonify({"error": "PrivacyManager no disponible"}), 503
    return jsonify(_saturday.privacy.get_state())


@vision_bp.route("/api/privacy", methods=["POST"])
@require_api_key
def privacy_set():
    if not _saturday or not _saturday.privacy:
        return jsonify({"error": "PrivacyManager no disponible"}), 503
    data = request.get_json(silent=True) or {}
    feature = data.get("feature", "")
    enabled = data.get("enabled")
    if not feature:
        return jsonify({"error": "feature es requerido"}), 400
    if enabled is not None:
        _saturday.privacy.set_enabled(feature, enabled)
    else:
        current = _saturday.privacy.get_state().get(feature, False)
        _saturday.privacy.set_enabled(feature, not current)
    return jsonify(_saturday.privacy.get_state())
