# backend/app.py - API para Saturday
import sys
import os
import base64
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import io

# Cargar variables de entorno
load_dotenv()

# Agregar la carpeta principal al path para importar modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.core import SaturdayCore

app = Flask(__name__)
CORS(app)

# Inicializar Saturday (una sola vez)
print("=" * 50)
print("🟣 SATURDAY - Backend API")
print("=" * 50)
print("⏳ Inicializando Saturday Core...")
saturday = SaturdayCore()
print("✅ Saturday Core inicializado correctamente")
print("=" * 50)


@app.route('/api/status', methods=['GET'])
def status():
    """Verifica el estado del sistema"""
    return jsonify({
        'status': 'online',
        'version': '3.1.0',
        'modules': {
            'notion': saturday.notion is not None,
            'calendar': saturday.calendar is not None,
            'email': saturday.email is not None,
            'voice': saturday.voice is not None,
            'data': saturday.data is not None,
        }
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Procesa un mensaje y devuelve respuesta"""
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Mensaje vacío'}), 400
    
    try:
        result = saturday.process_intent(message)
        return jsonify({
            'response': result['response'],
            'intent': result.get('intent', 'general'),
            'action': result.get('action', False)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/speak', methods=['POST'])
def speak():
    """Genera audio a partir de texto usando Google TTS"""
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Texto vacío'}), 400
    
    try:
        # Verificar que el voice manager esté disponible
        if not saturday.voice:
            return jsonify({'error': 'VoiceManager no disponible'}), 500
        
        # Generar audio usando Google TTS
        audio_data = saturday.voice._synthesize_google_tts(text)
        
        if audio_data:
            # Codificar en base64 para enviar al frontend
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return jsonify({
                'audio': audio_base64,
                'format': 'mp3'
            })
        else:
            return jsonify({'error': 'No se pudo generar el audio'}), 500
            
    except Exception as e:
        print(f"❌ Error en /api/speak: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Obtiene tareas de Notion"""
    result = saturday.process_intent('tareas')
    return jsonify({'response': result['response']})


@app.route('/api/events', methods=['GET'])
def get_events():
    """Obtiene eventos del calendario"""
    result = saturday.process_intent('eventos')
    return jsonify({'response': result['response']})


@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Obtiene notas guardadas"""
    result = saturday.process_intent('ver notas')
    return jsonify({'response': result['response']})


@app.route('/api/health', methods=['GET'])
def health():
    """Health check para despliegue"""
    return jsonify({'status': 'ok'})

@app.route('/api/stt', methods=['POST'])
def stt():
    """Reconoce voz desde un archivo de audio usando Google Cloud STT"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No se envió archivo de audio'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'Archivo vacío'}), 400
        
        import tempfile
        import os
        
        # Guardar el archivo temporalmente con la extensión original
        filename = audio_file.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_path = tmp_file.name
            audio_file.save(tmp_path)
        
        print(f"📁 Archivo guardado: {tmp_path} (ext: {ext})")
        
        # Verificar si es WEBM y forzar conversión
        is_webm = ext == '.webm' or 'webm' in filename
        
        if is_webm:
            print("🔄 Detectado formato WEBM, forzando conversión...")
            # Usar VoiceManager que tiene pydub
            if not saturday.voice:
                return jsonify({'error': 'VoiceManager no disponible'}), 500
            
            text = saturday.voice.recognize_audio_file(tmp_path)
        else:
            # Para otros formatos, intentar directamente
            if not saturday.voice:
                return jsonify({'error': 'VoiceManager no disponible'}), 500
            
            text = saturday.voice.recognize_audio_file(tmp_path)
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass
        
        if text:
            return jsonify({'text': text, 'success': True})
        else:
            return jsonify({'error': 'No se pudo reconocer el audio', 'success': False}), 400
            
    except Exception as e:
        print(f"❌ Error en /api/stt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stt-base64', methods=['POST'])
def stt_base64():
    """
    Reconoce voz desde audio en base64 usando Google Cloud STT
    """
    data = request.json
    audio_base64 = data.get('audio', '')
    
    if not audio_base64:
        return jsonify({'error': 'No se envió audio'}), 400
    
    try:
        # Decodificar base64
        audio_data = base64.b64decode(audio_base64)
        
        # Guardar temporalmente
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(audio_data)
        
        # Reconocer con Google STT
        if not saturday.voice:
            return jsonify({'error': 'VoiceManager no disponible'}), 500
        
        text = saturday.voice.recognize_audio_file(tmp_path)
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if text:
            return jsonify({
                'text': text,
                'success': True
            })
        else:
            return jsonify({
                'error': 'No se pudo reconocer el audio',
                'success': False
            }), 400
            
    except Exception as e:
        print(f"❌ Error en /api/stt-base64: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Servidor API iniciado en http://localhost:{port}")
    print("   Presiona Ctrl+C para detener")
    app.run(host='0.0.0.0', port=port, debug=True)