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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Servidor API iniciado en http://localhost:{port}")
    print("   Presiona Ctrl+C para detener")
    app.run(host='0.0.0.0', port=port, debug=True)