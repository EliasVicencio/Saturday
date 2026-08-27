# backend/app.py - API para Saturday COMPLETA
import sys
import os
import base64
import hmac
import logging
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import io
import threading
import hashlib
import time
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# ===== LOGGING ESTRUCTURADO =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('saturday')

# Agregar la carpeta principal al path para importar modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.core import SaturdayCore
from modules.input_validator import validate_message, validate_text, validate_search_query, validate_category, validate_limit, validate_audio_file, validate_vault_path, validate_vault_layer, validate_note_input

app = Flask(__name__)
CORS(app, origins=["https://saturday.viewdns.net", "http://localhost:5173"])
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per minute"])

# ===== API KEY AUTH =====
API_KEY = os.getenv("SATURDAY_API_KEY", "")
logger.info(f"API key loaded: {'yes' if API_KEY else 'NO - auth disabled'}")

def require_api_key(f):
    """Decorador que exige X-API-Key valida. Si no hay API_KEY configurada, rechaza."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_KEY:
            logger.warning("API key no configurada - rechazando request")
            return jsonify({"error": "Server misconfigured"}), 503
        key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(key, API_KEY):
            logger.warning(f"API key invalida desde {request.remote_addr} path={request.path}")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ===== SALUDO DE BIENVENIDA =====
# Guardamos el mensaje aquÃ­; el FRONTEND lo pide vÃ­a /api/greeting y lo
# reproduce en el navegador (a travÃ©s de /api/speak), igual que cualquier
# otra respuesta. Antes esto se reproducÃ­a en el propio servidor con
# subprocess/mpg123 y dejaba un .mp3 temporal en el disco del backend,
# lo cual no tiene relaciÃ³n con el navegador del usuario.
_greeting_message = {"text": None, "ready": False}

def build_welcome_message(core):
    """Arma el texto de saludo (clima incluido) sin reproducir audio en el servidor."""
    try:
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos dÃ­as"
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
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    temp = data['main']['temp']
                    desc = data['weather'][0]['description']
                    clima_info = f" Hoy en {city} hace {temp}Â°C con {desc}."
        except:
            pass

        mensaje = f"{saludo}! Soy Saturday, tu asistente personal.{clima_info} Estoy listo para ayudarte."
        _greeting_message["text"] = mensaje
        _greeting_message["ready"] = True
        logger.info(f"Saludo listo: {mensaje[:60]}...")
    except Exception as e:
        logger.error(f"Error preparando saludo: {e}")

# ===== INICIALIZAR SATURDAY =====
logger.info("=" * 50)
logger.info("SATURDAY - Backend API")
logger.info("=" * 50)
logger.info("Inicializando Saturday Core...")
_start_time = time.time()
saturday = SaturdayCore()
logger.info("Saturday Core inicializado correctamente")
logger.info("=" * 50)

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

@require_api_key
@app.route('/api/status', methods=['GET'])
def status():
    """Verifica el estado del sistema"""
    scheduler_running = False
    if saturday.scheduler:
        scheduler_running = saturday.scheduler.is_running
    
    return jsonify({
        'status': 'online',
        'version': '3.2.0',
        'modules': {
            'notion': saturday.notion is not None,
            'calendar': saturday.calendar is not None,
            'email': saturday.email is not None,
            'voice': saturday.voice is not None,
            'data': saturday.data is not None,
            'telegram': saturday.telegram is not None,
            'communication': saturday.communication is not None,
            'scheduler': scheduler_running,
            'spotify': saturday.spotify is not None,
            'news': saturday.news is not None,
            'conversation': saturday.conversation is not None,
        }
    })


@require_api_key
@limiter.limit('30 per minute')
@app.route('/api/chat', methods=['POST'])
def chat():
    """Procesa un mensaje y devuelve respuesta con contexto conversacional"""
    data = request.json
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'web_user')
    
    valid, err = validate_message(message)
    if not valid:
        return jsonify({'error': err}), 400
    
    try:
        chat_id = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % (10**9)
        result = saturday.process_intent(message, chat_id=chat_id)
        response_text = result['response']
        if response_text and saturday.voice:
            response_text = saturday.voice._fix_mojibake(response_text)
        response_payload = {
            'response': response_text,
            'intent': result.get('intent', 'general'),
            'action': result.get('action', False)
        }
        if result.get('navigate'):
            response_payload['navigate'] = result['navigate']
        return jsonify(response_payload)
    except Exception as e:
        logger.error(f"Error en /api/chat: {e}")
        return jsonify({'error': 'Error procesando mensaje'}), 500


@require_api_key
@app.route('/api/conversation/<session_id>', methods=['GET'])
def get_conversation(session_id):
    """Obtiene el historial de conversaciÃ³n de una sesiÃ³n"""
    if not saturday.conversation:
        return jsonify({'error': 'ConversationManager no disponible'}), 503
    
    chat_id = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % (10**9)
    ctx = saturday.conversation.get_context(chat_id)
    stats = saturday.conversation.get_stats(chat_id)
    
    return jsonify({
        'messages': ctx.get_recent_context(20),
        'stats': stats,
        'pending_question': ctx.pending_question,
    })


@require_api_key
@limiter.limit('10 per minute')
@app.route('/api/speak', methods=['POST'])
def speak():
    """Genera audio a partir de texto usando Google TTS"""
    data = request.json
    text = data.get('text', '').strip()
    
    valid, err = validate_text(text)
    if not valid:
        return jsonify({'error': err}), 400
    
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
        logger.error(f"Error en /api/speak: {e}")
        return jsonify({'error': 'Error generando audio'}), 500


@require_api_key
@limiter.limit('10 per minute')
@app.route('/api/stt', methods=['POST'])
def stt():
    """Reconoce voz desde un archivo de audio usando Google Cloud STT"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No se envio archivo de audio'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'Archivo vacio'}), 400
        
        import tempfile
        import os
        
        filename = audio_file.filename.lower()
        ext = os.path.splitext(filename)[1]
        
        valid_audio, audio_err = validate_audio_file(audio_file.filename, 0)
        if not valid_audio:
            return jsonify({'error': audio_err}), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            tmp_path = tmp_file.name
            audio_file.save(tmp_path)
        
        logger.info(f"Audio guardado: {tmp_path} (ext: {ext})")
        
        if not saturday.voice:
            return jsonify({'error': 'VoiceManager no disponible'}), 500
        
        text = saturday.voice.recognize_audio_file(tmp_path)
        
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
        
        if text:
            return jsonify({'text': text, 'success': True})
        else:
            return jsonify({'error': 'No se pudo reconocer el audio', 'success': False}), 400
            
    except Exception as e:
        logger.error(f"Error en /api/stt: {e}")
        return jsonify({'error': 'Error procesando audio'}), 500


@require_api_key
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Obtiene tareas de Notion (texto, para el chat/voz)"""
    result = saturday.process_intent('tareas')
    return jsonify({'response': result['response']})


@require_api_key
@app.route('/api/tasks/list', methods=['GET'])
def get_tasks_list():
    """Tareas pendientes de Notion en formato estructurado (para el dashboard)"""
    if not saturday.notion:
        return jsonify({'tasks': []})
    try:
        tasks = saturday.notion.get_tasks(status="Todo", limit=8)
        return jsonify({'tasks': [{'title': t.get('name', 'Sin titulo')} for t in tasks]})
    except Exception as e:
        logger.error(f"Error obteniendo tareas: {e}")
        return jsonify({'tasks': [], 'error': 'Error obteniendo tareas'})


@require_api_key
@app.route('/api/events', methods=['GET'])
def get_events():
    """Obtiene eventos del calendario (texto, para el chat/voz)"""
    result = saturday.process_intent('eventos')
    return jsonify({'response': result['response']})


@require_api_key
@app.route('/api/events/today', methods=['GET'])
def get_events_today():
    """Eventos de hoy en formato estructurado (para el dashboard)"""
    if not saturday.calendar:
        return jsonify({'events': []})
    try:
        events = saturday.calendar.get_events_today_list()
        return jsonify({'events': events})
    except Exception as e:
        logger.error(f"Error obteniendo eventos: {e}")
        return jsonify({'events': [], 'error': 'Error obteniendo eventos'})


@require_api_key
@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Obtiene notas guardadas"""
    result = saturday.process_intent('ver notas')
    return jsonify({'response': result['response']})


@require_api_key
@app.route('/api/whatsapp', methods=['POST'])
def send_whatsapp():
    """EnvÃ­a mensaje por WhatsApp"""
    data = request.json
    message = data.get('message', 'Hola desde Saturday')
    
    if not saturday.communication:
        return jsonify({'error': 'CommunicationManager no disponible'}), 500
    
    result = saturday.communication.send_whatsapp_message(message)
    
    if result.get('success'):
        return jsonify({'success': True, 'message': 'WhatsApp enviado'})
    else:
        return jsonify({'success': False, 'error': result.get('error')}), 500


@require_api_key
@app.route('/api/whatsapp/voice', methods=['POST'])
def send_whatsapp_voice():
    """EnvÃ­a mensaje de voz por WhatsApp"""
    data = request.json
    message = data.get('message', 'Hola desde Saturday')
    
    if not saturday.communication:
        return jsonify({'error': 'CommunicationManager no disponible'}), 500
    
    result = saturday.communication.send_whatsapp_voice(message)
    
    if result.get('success'):
        return jsonify({'success': True, 'message': 'WhatsApp con voz enviado'})
    else:
        return jsonify({'success': False, 'error': result.get('error')}), 500


@require_api_key
@app.route('/api/summary', methods=['POST'])
def send_summary():
    """EnvÃ­a el resumen del dÃ­a por WhatsApp"""
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


@require_api_key
@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Inicia el scheduler"""
    if not saturday.scheduler:
        return jsonify({'error': 'Scheduler no disponible'}), 500
    
    saturday.scheduler.start()
    return jsonify({'success': True, 'message': 'Scheduler iniciado'})


@require_api_key
@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Detiene el scheduler"""
    if not saturday.scheduler:
        return jsonify({'error': 'Scheduler no disponible'}), 500
    
    saturday.scheduler.stop()
    return jsonify({'success': True, 'message': 'Scheduler detenido'})


@require_api_key
@app.route('/api/weather', methods=['GET'])
def weather():
    """Devuelve el clima actual en formato estructurado para el dashboard"""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        city = os.getenv("SATURDAY_CITY", "Santiago")
        if not api_key:
            return jsonify({'error': 'WEATHER_API_KEY no configurada'}), 500

        import requests
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
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
        logger.error(f"Error en /api/weather: {e}")
        return jsonify({'error': 'Error obteniendo clima'}), 500


@require_api_key
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
        return jsonify({'error': 'psutil no disponible'}), 500
    except Exception as e:
        logger.error(f"Error en /api/system: {e}")
        return jsonify({'error': 'Error obteniendo metricas'}), 500
    
@require_api_key
@app.route('/api/news', methods=['GET'])
def news():
    """Devuelve las noticias principales"""
    try:
        result = saturday.get_news()
        return jsonify({'response': result})
    except Exception as e:
        logger.error(f"Error en /api/news: {e}")
        return jsonify({'error': 'Error obteniendo noticias'}), 500


@require_api_key
@app.route('/api/news/headlines', methods=['GET'])
def news_headlines():
    """Titulares en formato estructurado"""
    if not saturday.news or not saturday.news.is_available():
        return jsonify({'articles': [], 'available': False})
    try:
        category = request.args.get('category')
        valid, limit, err = validate_limit(request.args.get('limit', 8))
        if not valid:
            return jsonify({'articles': [], 'error': err}), 400
        articles = saturday.news.get_top_headlines(category=category, limit=limit)
        return jsonify({'articles': articles, 'available': True})
    except Exception as e:
        logger.error(f"Error en /api/news/headlines: {e}")
        return jsonify({'articles': [], 'available': True, 'error': 'Error obteniendo titulares'})


@require_api_key
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
        logger.error(f"Error en /api/crypto: {e}")
        return jsonify({'error': 'Error obteniendo precio Bitcoin'}), 500

    
@require_api_key
@limiter.limit('20 per minute')
@app.route('/api/youtube/search', methods=['GET'])
def youtube_search():
    """Busca videos en YouTube. ?q=termino&max_results=5"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        return jsonify({'error': 'YOUTUBE_API_KEY no configurada'}), 500
    
    valid_q, err_q = validate_search_query(request.args.get('q', ''))
    if not valid_q:
        return jsonify({'error': err_q}), 400
    query = request.args.get('q', '').strip()
    
    valid_limit, max_results, err_limit = validate_limit(request.args.get('max_results', 5), max_val=10)
    if not valid_limit:
        max_results = 5
    
    try:
        url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': api_key,
            'relevanceLanguage': 'es',
            'order': 'relevance',
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        videos = []
        for item in data.get('items', []):
            snippet = item['snippet']
            videos.append({
                'id': item['id']['videoId'],
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'thumbnail': snippet['thumbnails']['medium']['url'],
                'published': snippet['publishedAt'],
            })
        
        return jsonify({'videos': videos, 'query': query})
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error YouTube API: {e}")
        return jsonify({'error': 'Error de YouTube API'}), 502
    except Exception as e:
        logger.error(f"Error en /api/youtube: {e}")
        return jsonify({'error': 'Error buscando videos'}), 500


@require_api_key
@app.route('/api/camera', methods=['GET'])
def camera():
    """Devuelve el estado de la camara"""
    try:
        if saturday.camera:
            result = saturday.camera.get_status()
            return jsonify({'success': True, 'data': result})
        return jsonify({'success': False, 'error': 'CameraManager no disponible'})
    except Exception as e:
        logger.error(f"Error en /api/camera: {e}")
        return jsonify({'error': 'Error obteniendo estado de camara'}), 500

@require_api_key
@app.route('/api/vault/stats', methods=['GET'])
def vault_stats():
    """Resumen de la boveda"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    return jsonify(saturday.vault.get_stats())


@require_api_key
@app.route('/api/vault/notes', methods=['GET'])
def vault_notes():
    """Lista las notas de una capa: ?layer=raw|wiki|outputs"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    layer = request.args.get('layer', 'wiki')
    valid, err = validate_vault_layer(layer)
    if not valid:
        return jsonify({'error': err}), 400
    return jsonify({'layer': layer, 'notes': saturday.vault.list_notes(layer)})


@require_api_key
@app.route('/api/vault/note', methods=['GET'])
def vault_note():
    """Devuelve el contenido de una nota: ?path=wiki/mi-nota.md"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    path = request.args.get('path')
    if not path:
        return jsonify({'error': "Falta el parametro 'path'"}), 400
    valid, err = validate_vault_path(path)
    if not valid:
        return jsonify({'error': err}), 400
    content = saturday.vault.read_note(path)
    if content is None:
        return jsonify({'error': 'Nota no encontrada'}), 404
    return jsonify({'path': path, 'content': content})


@require_api_key
@app.route('/api/vault/note', methods=['POST'])
def vault_create_note():
    """Crea/actualiza una nota en wiki/. Body: {title, content, tags?}"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    data = request.json or {}
    valid, err = validate_note_input(data)
    if not valid:
        return jsonify({'error': err}), 400
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    tags = data.get('tags', [])
    path = saturday.vault.create_wiki_note(title, content, tags)
    return jsonify({'success': True, 'path': path})


@require_api_key
@app.route('/api/vault/search', methods=['GET'])
def vault_search():
    """Busca texto en toda la boveda: ?q=termino"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': "Falta el parametro 'q'"}), 400
    return jsonify({'query': query, 'results': saturday.vault.search(query)})


@require_api_key
@app.route('/api/vault/graph', methods=['GET'])
def vault_graph():
    """Grafo de notas enlazadas (nodes/edges) para visualizar en el frontend"""
    if not saturday.vault:
        return jsonify({'error': 'VaultManager no disponible'}), 500
    return jsonify(saturday.vault.get_graph_json())


@app.route('/api/health', methods=['GET'])
def health():
    """Health check con metricas del sistema"""
    import psutil
    uptime = time.time() - _start_time if '_start_time' in dir() else 0
    health_data = {
        'status': 'ok',
        'version': '3.2.0',
        'uptime_seconds': int(uptime),
        'modules': {
            'notion': saturday.notion is not None,
            'voice': saturday.voice is not None,
            'calendar': saturday.calendar is not None,
            'conversation': saturday.conversation is not None,
        }
    }
    try:
        health_data['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        health_data['ram_percent'] = psutil.virtual_memory().percent
    except Exception:
        pass
    return jsonify(health_data)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    # Iniciar scheduler
    if saturday.scheduler:
        saturday.scheduler.start()
        hour = int(os.getenv('SUMMARY_HOUR', 20))
        minute = int(os.getenv('SUMMARY_MINUTE', 0))
        saturday.scheduler.schedule_daily_summary(hour, minute)
        logger.info(f"Resumen diario programado para las {hour:02d}:{minute:02d}")
    
    logger.info("SATURDAY API INICIADA")
    logger.info(f"Puerto: {port}")
    logger.info(f"WhatsApp: {'Activo' if saturday.communication and saturday.communication.whatsapp_enabled else 'Inactivo'}")
    logger.info(f"Scheduler: {'Activo' if saturday.scheduler else 'Inactivo'}")
    
    app.run(host="127.0.0.1", port=port, debug=False)
