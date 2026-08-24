# backend/app.py - API para Saturday COMPLETA
import sys
import os
import base64
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import io
import threading
import time
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Agregar la carpeta principal al path para importar modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.core import SaturdayCore

app = Flask(__name__)
CORS(app)

# ===== SALUDO DE BIENVENIDA =====
# Guardamos el mensaje aquí; el FRONTEND lo pide vía /api/greeting y lo
# reproduce en el navegador (a través de /api/speak), igual que cualquier
# otra respuesta. Antes esto se reproducía en el propio servidor con
# subprocess/mpg123 y dejaba un .mp3 temporal en el disco del backend,
# lo cual no tiene relación con el navegador del usuario.
_greeting_message = {"text": None, "ready": False}

def build_welcome_message(core):
    """Arma el texto de saludo (clima incluido) sin reproducir audio en el servidor."""
    try:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos días"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        clima_info = ""
        try:
            import requests
            api_key = os.getenv("WEATHER_API_KEY")
            city = os.getenv("SATURDAY_CITY", "Santiago")
            if api_key:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    desc = data['weather'][0]['description']
                    clima_info = f" Hoy en {city} hace {temp}°C con {desc}."
        except:
            pass

        mensaje = f"{saludo}! Soy Saturday, tu asistente personal.{clima_info} Estoy listo para ayudarte."
        _greeting_message["text"] = mensaje
        _greeting_message["ready"] = True
        print(f"🗣️ Saludo listo para el frontend: {mensaje}")
    except Exception as e:
        print(f"⚠️ Error preparando saludo: {e}")

# ===== INICIALIZAR SATURDAY =====
print("=" * 50)
print("🟣 SATURDAY - Backend API")
print("=" * 50)
print("⏳ Inicializando Saturday Core...")
saturday = SaturdayCore()
print("✅ Saturday Core inicializado correctamente")
print("=" * 50)

# ===== PREPARAR SALUDO (sin tocar el audio del servidor) =====
saludo_thread = threading.Thread(target=build_welcome_message, args=(saturday,), daemon=True)
saludo_thread.start()


@app.route('/api/greeting', methods=['GET'])
def greeting():
    """Devuelve el texto de saludo para que el FRONTEND lo pida y lo hable
    en el navegador del usuario (usando /api/speak), en vez de sonar en el
    servidor."""
    return jsonify({
        'ready': _greeting_message['ready'],
        'text': _greeting_message['text'],
    })

# ===== ENDPOINTS =====

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
            'spotify': saturday.spotify is not None,
            'news': saturday.news is not None,
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
    """Obtiene tareas de Notion (texto, para el chat/voz)"""
    result = saturday.process_intent('tareas')
    return jsonify({'response': result['response']})


@app.route('/api/tasks/list', methods=['GET'])
def get_tasks_list():
    """Tareas pendientes de Notion en formato estructurado (para el dashboard)"""
    if not saturday.notion:
        return jsonify({'tasks': []})
    try:
        tasks = saturday.notion.get_tasks(status="Todo", limit=8)
        return jsonify({'tasks': [{'title': t.get('name', 'Sin título')} for t in tasks]})
    except Exception as e:
        return jsonify({'tasks': [], 'error': str(e)})


@app.route('/api/events', methods=['GET'])
def get_events():
    """Obtiene eventos del calendario (texto, para el chat/voz)"""
    result = saturday.process_intent('eventos')
    return jsonify({'response': result['response']})


@app.route('/api/events/today', methods=['GET'])
def get_events_today():
    """Eventos de hoy en formato estructurado (para el dashboard)"""
    if not saturday.calendar:
        return jsonify({'events': []})
    try:
        events = saturday.calendar.get_events_today_list()
        return jsonify({'events': events})
    except Exception as e:
        return jsonify({'events': [], 'error': str(e)})


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
        return jsonify({
            'success': True,
            'message': 'Resumen enviado',
            'vault_path': result.get('vault_path'),
        })
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


@app.route('/api/weather', methods=['GET'])
def weather():
    """Devuelve el clima actual en formato estructurado para el dashboard"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        city = os.getenv("SATURDAY_CITY", "Santiago")
        if not api_key:
            return jsonify({'error': 'No configuraste WEATHER_API_KEY'}), 500

        import requests
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Error obteniendo el clima'}), 502

        data = response.json()
        return jsonify({
            'temp': round(data['main']['temp'], 1),
            'feels_like': round(data['main']['feels_like'], 1),
            'condition': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind': data['wind']['speed'],
            'city': data.get('name', city),
            'country': data.get('sys', {}).get('country', ''),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/system', methods=['GET'])
def system_stats():
    """Devuelve uso real de CPU, RAM y disco del servidor"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return jsonify({
            'cpu_percent': cpu,
            'ram_percent': mem.percent,
            'ram_used_gb': round(mem.used / (1024 ** 3), 1),
            'ram_total_gb': round(mem.total / (1024 ** 3), 1),
            'disk_used_gb': round(disk.used / (1024 ** 3), 1),
            'disk_total_gb': round(disk.total / (1024 ** 3), 1),
        })
    except ImportError:
        return jsonify({'error': 'psutil no está instalado en el backend'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/news', methods=['GET'])
def news():
    """Devuelve las noticias principales"""
    try:
        result = saturday.get_news()
        return jsonify({'response': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/news/headlines', methods=['GET'])
def news_headlines():
    """
    Titulares en formato estructurado (título, fuente, url, imagen, categoría),
    sin pasar por texto formateado. ?category=technology&limit=8
    """
    if not saturday.news or not saturday.news.is_available():
        return jsonify({'articles': [], 'available': False})
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 8))
        articles = saturday.news.get_top_headlines(category=category, limit=limit)
        return jsonify({'articles': articles, 'available': True})
    except Exception as e:
        return jsonify({'articles': [], 'available': True, 'error': str(e)})


@app.route('/api/crypto/bitcoin', methods=['GET'])
def crypto_bitcoin():
    """Precio actual de Bitcoin (CoinGecko, sin necesidad de API key)"""
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd,clp",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json().get("bitcoin", {})
        if not data:
            return jsonify({'error': 'Sin datos de CoinGecko'}), 502
        return jsonify({
            'usd': data.get('usd'),
            'clp': data.get('clp'),
            'usd_24h_change': round(data.get('usd_24h_change', 0), 2),
            'last_updated_at': data.get('last_updated_at'),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/camera', methods=['GET'])
def camera():
    """Devuelve el estado de la cámara"""
    try:
        if saturday.camera:
            result = saturday.camera.get_status()
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'CameraManager no disponible'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vault/stats', methods=['GET'])
def vault_stats():
    """Resumen de la bóveda: cuántas notas hay en raw/, wiki/, outputs/ y el grafo"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    return jsonify(saturday.vault.get_stats())


@app.route('/api/vault/notes', methods=['GET'])
def vault_notes():
    """Lista las notas de una capa: ?layer=raw|wiki|outputs"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    layer = request.args.get('layer', 'wiki')
    return jsonify({'layer': layer, 'notes': saturday.vault.list_notes(layer)})


@app.route('/api/vault/note', methods=['GET'])
def vault_note():
    """Devuelve el contenido de una nota: ?path=wiki/mi-nota.md"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    path = request.args.get('path')
    if not path:
        return jsonify({'error': "Falta el parámetro 'path'"}), 400
    content = saturday.vault.read_note(path)
    if content is None:
        return jsonify({'error': 'Nota no encontrada'}), 404
    return jsonify({'path': path, 'content': content})


@app.route('/api/vault/note', methods=['POST'])
def vault_create_note():
    """Crea/actualiza una nota en wiki/. Body: {title, content, tags?}"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    data = request.json or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    tags = data.get('tags', [])
    if not title or not content:
        return jsonify({'error': "Se requieren 'title' y 'content'"}), 400
    path = saturday.vault.create_wiki_note(title, content, tags)
    return jsonify({'success': True, 'path': path})


@app.route('/api/vault/search', methods=['GET'])
def vault_search():
    """Busca texto en toda la bóveda: ?q=término"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': "Falta el parámetro 'q'"}), 400
    return jsonify({'query': query, 'results': saturday.vault.search(query)})


@app.route('/api/vault/graph', methods=['GET'])
def vault_graph():
    """Grafo de notas enlazadas (nodes/edges) para visualizar en el frontend"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    return jsonify(saturday.vault.get_graph_json())


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
    print("  GET  /api/greeting    - Texto de saludo (lo habla el frontend)")
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