# api/voice.py - Voice (TTS/STT) Blueprint
from flask import Blueprint, request, jsonify
import logging
import tempfile

logger = logging.getLogger('saturday.voice')

voice_bp = Blueprint('voice', __name__)

_saturday = None

def init_voice(saturday):
    global _saturday
    _saturday = saturday

@voice_bp.route('/api/speak', methods=['POST'])
def speak():
    from api.auth import require_api_key
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if len(text) > 300:
        text = text[:297] + "..."
    
    audio_data = _saturday.voice.speak(text)
    if audio_data:
        return audio_data, 200, {'Content-Type': 'audio/mp3', 'Content-Disposition': 'inline'}
    return jsonify({'error': 'Error generando audio'}), 500

@voice_bp.route('/api/stt', methods=['POST'])
def stt():
    from api.auth import require_api_key
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        audio_file.save(tmp.name)
        text = _saturday.voice.transcribe(tmp.name)
    
    import os
    try:
        os.unlink(tmp.name)
    except OSError:
        pass
    
    return jsonify({'text': text or ''})
