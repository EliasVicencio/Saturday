# backend/tests/test_google_stt.py
import os
import sys
import base64
import requests
import json

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

print("=" * 60)
print("🧪 TEST DE GOOGLE CLOUD STT")
print("=" * 60)

# Verificar API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY no encontrada")
    sys.exit(1)

print(f"✅ API Key: {api_key[:10]}...")

# ===== PRUEBA 1: Test con audio de ejemplo (usando la API directamente) =====
print("\n" + "=" * 60)
print("📝 PRUEBA 1: Test con petición directa a Google STT")
print("=" * 60)

# Crear un archivo de audio de prueba (silencioso) para verificar la conexión
# Esto solo prueba que la API key funciona, no que reconozca voz
url = "https://speech.googleapis.com/v1/speech:recognize"
headers = {
    "X-Goog-Api-Key": api_key,
    "Content-Type": "application/json"
}

# Crear un audio mudo de 1 segundo (16000 muestras) en base64
# Esto es solo para probar la conexión, no para reconocer voz real
import wave
import io
import struct

# Generar audio silencioso
sample_rate = 16000
duration = 0.5  # medio segundo
num_samples = int(sample_rate * duration)

# Crear buffer de audio en WAV
buffer = io.BytesIO()
with wave.open(buffer, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    # Escribir silencio
    silence = struct.pack('<h', 0) * num_samples
    wf.writeframes(silence)

audio_bytes = buffer.getvalue()
audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

payload = {
    "config": {
        "encoding": "LINEAR16",
        "sampleRateHertz": 16000,
        "languageCode": "es-ES",
        "enableAutomaticPunctuation": True,
    },
    "audio": {
        "content": audio_base64
    }
}

print("📤 Enviando petición a Google STT (audio silencioso)...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"📊 Código de respuesta: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Conexión con Google STT exitosa")
        print(f"📝 Respuesta: {response.json()}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Error en la petición: {e}")

# ===== PRUEBA 2: Test con archivo de audio real (si existe) =====
print("\n" + "=" * 60)
print("📝 PRUEBA 2: Test con archivo de audio real")
print("=" * 60)

# Buscar un archivo de audio en el sistema
audio_files = [
    "test_audio.mp3",
    "test_audio.wav",
    "saturday_voice.mp3",
    os.path.join(current_dir, "test_audio.mp3"),
    os.path.join(current_dir, "test_audio.wav"),
]

audio_file = None
for f in audio_files:
    if os.path.exists(f):
        audio_file = f
        break

if audio_file:
    print(f"✅ Archivo encontrado: {audio_file}")
    
    try:
        # Leer el archivo
        with open(audio_file, "rb") as f:
            audio_data = f.read()
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Detectar formato por extensión
        ext = os.path.splitext(audio_file)[1].lower()
        is_wav = ext == '.wav'
        
        # Configuración según formato
        if is_wav:
            config = {
                "encoding": "LINEAR16",
                "sampleRateHertz": 16000,
                "languageCode": "es-ES",
                "enableAutomaticPunctuation": True,
            }
        else:
            # Para MP3 u otros formatos, Google puede no soportarlos directamente
            config = {
                "encoding": "LINEAR16",
                "languageCode": "es-ES",
                "enableAutomaticPunctuation": True,
            }
        
        payload = {
            "config": config,
            "audio": {"content": audio_base64}
        }
        
        print(f"📤 Enviando archivo {ext} a Google STT...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"📊 Código: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                transcript = data["results"][0]["alternatives"][0]["transcript"]
                print(f"✅ Texto reconocido: '{transcript}'")
            else:
                print("⚠️ No se reconoció texto")
        else:
            print(f"❌ Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
else:
    print("⚠️ No se encontró un archivo de audio para probar")
    print("   Puedes probar con un archivo WAV manualmente")

# ===== PRUEBA 3: Test con VoiceManager =====
print("\n" + "=" * 60)
print("📝 PRUEBA 3: Test con VoiceManager")
print("=" * 60)

try:
    from modules.voice import VoiceManager
    voice = VoiceManager()
    
    if voice.use_google:
        print("✅ Google TTS/STT habilitado")
        print(f"🔑 API Key: {voice.api_key[:10]}...")
        print(f"🎤 Voz: {voice.voice_name}")
    else:
        print("⚠️ Google no está habilitado")
        
except Exception as e:
    print(f"❌ Error importando VoiceManager: {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO")
print("=" * 60)