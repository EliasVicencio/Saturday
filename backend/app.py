# backend/app.py - API para Saturday COMPLETA
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
            'telegram': saturday.telegram is not None,
            'communication': saturday.communication is not None,
            'scheduler': saturday.scheduler is not None,
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
        if not saturday.voice:
            return jsonify({'error': 'VoiceManager no disponible'}), 500
        
        audio_data = saturday.voice._synthesize_google_tts(text)
        
        if audio_data:
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
        
        filename = audio_file.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_path = tmp_file.name
            audio_file.save(tmp_path)
        
        print(f"📁 Archivo guardado: {tmp_path} (ext: {ext})")
        
        if not saturday.voice:
            return jsonify({'error': 'VoiceManager no disponible'}), 500
        
        text = saturday.voice.recognize_audio_file(tmp_path)
        
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


@app.route('/api/whatsapp', methods=['POST'])
def send_whatsapp():
    """Envía mensaje por WhatsApp"""
    data = request.json
    message = data.get('message', 'Hola desde Saturday')
    
    if not saturday.communication:
        return jsonify({'error': 'CommunicationManager no disponible'}), 500
    
    result = saturday.communication.send_whatsapp_message(message)
    
    if result.get('success'):
        return jsonify({'success': True, 'message': 'WhatsApp enviado'})
    else:
        return jsonify({'success': False, 'error': result.get('error')}), 500


@app.route('/api/whatsapp/voice', methods=['POST'])
def send_whatsapp_voice():
    """Envía mensaje de voz por WhatsApp"""
    data = request.json
    message = data.get('message', 'Hola desde Saturday')
    
    if not saturday.communication:
        return jsonify({'error': 'CommunicationManager no disponible'}), 500
    
    result = saturday.communication.send_whatsapp_voice(message)
    
    if result.get('success'):
        return jsonify({'success': True, 'message': 'WhatsApp con voz enviado'})
    else:
        return jsonify({'success': False, 'error': result.get('error')}), 500


@app.route('/api/summary', methods=['POST'])
def send_summary():
    """Envía el resumen del día por WhatsApp"""
    if not saturday.daily_summary:
        return jsonify({'error': 'DailySummary no disponible'}), 500
    
    result = saturday.daily_summary.send(via="whatsapp")
    
    if result.get('success'):
        return jsonify({'success': True, 'message': 'Resumen enviado'})
    else:
        return jsonify({'success': False, 'error': result.get('error')}), 500


@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Inicia el scheduler"""
    if not saturday.scheduler:
        return jsonify({'error': 'Scheduler no disponible'}), 500
    
    saturday.scheduler.start()
    return jsonify({'success': True, 'message': 'Scheduler iniciado'})


@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Detiene el scheduler"""
    if not saturday.scheduler:
        return jsonify({'error': 'Scheduler no disponible'}), 500
    
    saturday.scheduler.stop()
    return jsonify({'success': True, 'message': 'Scheduler detenido'})


@app.route('/api/health', methods=['GET'])
def health():
    """Health check para despliegue"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    # Iniciar scheduler automáticamente
    if saturday.scheduler:
        saturday.scheduler.start()
        hour = int(os.getenv('SUMMARY_HOUR', 20))
        minute = int(os.getenv('SUMMARY_MINUTE', 0))
        saturday.scheduler.schedule_daily_summary(hour, minute)
        print(f"📋 Resumen diario programado para las {hour:02d}:{minute:02d}")
    
    print("\n" + "=" * 50)
    print("🚀 SATURDAY API INICIADA")
    print("=" * 50)
    print(f"📡 Puerto: {port}")
    print(f"📱 WhatsApp: {'✅ Activado' if saturday.communication and saturday.communication.whatsapp_enabled else '❌ Inactivo'}")
    print(f"⏰ Scheduler: {'✅ Activo' if saturday.scheduler else '❌ Inactivo'}")
    print(f"📋 Resumen diario: {'✅ Programado' if saturday.scheduler else '❌ No programado'}")
    print("=" * 50)
    print("\n📋 Endpoints disponibles:")
    print("  GET  /api/status      - Estado del sistema")
    print("  POST /api/chat        - Enviar mensaje")
    print("  POST /api/speak       - Generar voz")
    print("  POST /api/stt         - Reconocer voz")
    print("  POST /api/whatsapp    - Enviar WhatsApp")
    print("  POST /api/whatsapp/voice - Enviar voz WhatsApp")
    print("  POST /api/summary     - Enviar resumen diario")
    print("  POST /api/scheduler/start - Iniciar scheduler")
    print("  POST /api/scheduler/stop  - Detener scheduler")
    print("  GET  /api/tasks       - Tareas de Notion")
    print("  GET  /api/events      - Eventos del calendario")
    print("  GET  /api/notes       - Notas guardadas")
    print("  GET  /api/health      - Health check")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True)