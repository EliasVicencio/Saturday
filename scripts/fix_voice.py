import base64

# Read original file
with open("/home/ubuntu/Saturday/backend/api/voice.py") as f:
    content = f.read()

# Fix 1: speak endpoint - return JSON {audio: base64} instead of raw bytes
old_speak = '''    audio_data = _saturday.voice.speak(text)
    if audio_data:
        return audio_data, 200, {'Content-Type': 'audio/mp3', 'Content-Disposition': 'inline'}
    return jsonify({'error': 'Error generando audio'}), 500'''

new_speak = '''    audio_data = _saturday.voice._synthesize_google_tts(text)
    if audio_data:
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        return jsonify({'audio': audio_b64, 'format': 'mp3'})
    return jsonify({'error': 'Error generando audio'}), 500'''

# Fix 2: stt endpoint - return success field + fix method name + fix file extension
old_stt = '''@voice_bp.route('/api/stt', methods=['POST'])
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
    
    return jsonify({'text': text or ''})'''

new_stt = '''@voice_bp.route('/api/stt', methods=['POST'])
def stt():
    from api.auth import require_api_key
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file', 'success': False}), 400
    
    audio_file = request.files['audio']
    suffix = os.path.splitext(audio_file.filename or 'audio.webm')[1] or '.webm'
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
    
    return jsonify({'text': text or '', 'success': bool(text)})'''

content = content.replace(old_speak, new_speak)
content = content.replace(old_stt, new_stt)

# Add missing import
if "import os" not in content.split("voice_bp")[0]:
    content = content.replace("import logging\nimport tempfile", "import logging\nimport tempfile\nimport os")

with open("/home/ubuntu/Saturday/backend/api/voice.py", "w") as f:
    f.write(content)

print("Fixed voice.py")
