# backend/tests/test_stt_real_voice.py
import os
import sys
import base64
import requests
import tempfile
import wave
import pyaudio
import struct

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

print("=" * 60)
print("🎤 TEST: GRABAR Y RECONOCER VOZ REAL")
print("=" * 60)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY no encontrada")
    sys.exit(1)

print(f"✅ API Key: {api_key[:10]}...")

# ===== PASO 1: Grabar voz desde el micrófono =====
print("\n🎤 Grabando voz desde el micrófono...")
print("   Di algo en los próximos 5 segundos...")

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

stream.stop_stream()
stream.close()
p.terminate()

print("✅ Grabación completada")

# ===== PASO 2: Guardar como WAV =====
wav_path = os.path.join(current_dir, "recorded_voice.wav")
with wave.open(wav_path, 'wb') as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))

print(f"✅ Audio guardado: {wav_path}")

# ===== PASO 3: Enviar a Google STT =====
print("\n📤 Enviando a Google STT...")

with open(wav_path, "rb") as f:
    audio_data = f.read()

audio_base64 = base64.b64encode(audio_data).decode('utf-8')

url = "https://speech.googleapis.com/v1/speech:recognize"
headers = {
    "X-Goog-Api-Key": api_key,
    "Content-Type": "application/json"
}
payload = {
    "config": {
        "encoding": "LINEAR16",
        "sampleRateHertz": 16000,
        "languageCode": "es-ES",
        "enableAutomaticPunctuation": True,
        "model": "latest_long",
        "useEnhanced": True
    },
    "audio": {
        "content": audio_base64
    }
}

response = requests.post(url, headers=headers, json=payload, timeout=30)
print(f"📊 Código de respuesta: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data.get("results"):
        transcript = data["results"][0]["alternatives"][0]["transcript"]
        print(f"\n✅ TEXTO RECONOCIDO: '{transcript}'")
    else:
        print("\n⚠️ No se reconoció texto. ¿Hablaste lo suficientemente claro?")
        print("   Respuesta completa:", data)
else:
    print(f"\n❌ Error: {response.text}")

# ===== PASO 4: Limpiar =====
try:
    os.unlink(wav_path)
    print(f"\n🧹 Archivo eliminado: {wav_path}")
except:
    pass

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO")
print("=" * 60)