# api/voice.py - Voice (TTS/STT) Blueprint
from flask import Blueprint, request, jsonify
from api.auth import require_api_key
import logging
import tempfile
import os
import base64

logger = logging.getLogger("saturday.voice")

voice_bp = Blueprint("voice", __name__)

_saturday = None


def init_voice(saturday):
    global _saturday
    _saturday = saturday


@voice_bp.route("/api/speak", methods=["POST"])
@require_api_key
def speak():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Google Cloud TTS soporta hasta ~5000 caracteres por pedido. El limite
    # anterior (300) cortaba a mitad de frase cualquier respuesta con opinion
    # o explicacion un poco mas larga. Si aun asi hay que cortar (mensajes
    # extremadamente largos), se corta en el ultimo punto/salto de linea
    # antes del limite, no a mitad de palabra.
    MAX_TTS_CHARS = 4500
    if len(text) > MAX_TTS_CHARS:
        cutoff = text.rfind(".", 0, MAX_TTS_CHARS)
        if cutoff == -1 or cutoff < MAX_TTS_CHARS * 0.5:
            cutoff = MAX_TTS_CHARS
        else:
            cutoff += 1
        text = text[:cutoff].strip()

    audio_data = _saturday.voice._synthesize_google_tts(text)
    if audio_data:
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")
        return jsonify({"audio": audio_b64, "format": "mp3"})
    return jsonify({"error": "Error generando audio"}), 500


@voice_bp.route("/api/stt", methods=["POST"])
@require_api_key
def stt():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file", "success": False}), 400

    audio_file = request.files["audio"]
    suffix = os.path.splitext(audio_file.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        text = _saturday.voice.recognize_audio_file(tmp_path)
    except Exception as e:
        logger.error("STT error: %s", e)
        text = None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return jsonify({"text": text or "", "success": bool(text)})
