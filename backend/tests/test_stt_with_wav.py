# backend/tests/test_stt_with_wav.py
import os
import sys
import base64
import requests
import wave
import numpy as np
import tempfile

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(backend_dir))

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

print("=" * 60)
print("🎤 TEST: Crear WAV y enviar a Google STT")
print("=" * 60)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY no encontrada")
    sys.exit(1)

print(f"✅ API Key: {api_key[:10]}...")

# ===== PASO 1: Crear un archivo WAV de prueba con voz artificial =====
print("\n📝 Creando archivo WAV de prueba...")

# Crear un tono simple (simulación de voz)
sample_rate = 16000
duration = 2  # segundos
frequency = 440  # Hz (nota La)

# Generar datos de audio
t = np.linspace(0, duration, int(sample_rate * duration))
audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

# Guardar como WAV
wav_path = os.path.join(current_dir, "test_audio.wav")
with wave.open(wav_path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_data.tobytes())

print(f"✅ Archivo WAV creado: {wav_path}")

# ===== PASO 2: Enviar a Google STT =====
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
    },
    "audio": {
        "content": audio_base64
    }
}

response = requests.post(url, headers=headers, json=payload, timeout=15)
print(f"📊 Código de respuesta: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data.get("results"):
        transcript = data["results"][0]["alternatives"][0]["transcript"]
        print(f"✅ Texto reconocido: '{transcript}'")
    else:
        print("⚠️ No se reconoció texto (es normal si es solo un tono)")
        print(f"📝 Respuesta completa: {data}")
else:
    print(f"❌ Error: {response.text}")

# ===== PASO 3: Probar con el VoiceManager =====
print("\n" + "=" * 60)
print("📝 Probando con VoiceManager...")
print("=" * 60)

try:
    from modules.voice import VoiceManager
    voice = VoiceManager()
    
    print("\n🎤 Reconociendo con VoiceManager...")
    text = voice.recognize_audio_file(wav_path)
    
    if text:
        print(f"✅ VoiceManager reconoció: '{text}'")
    else:
        print("⚠️ VoiceManager no reconoció texto (es normal si es solo un tono)")
        
except Exception as e:
    print(f"❌ Error: {e}")

# ===== PASO 4: Limpiar =====
try:
    os.unlink(wav_path)
    print(f"\n🧹 Archivo WAV eliminado: {wav_path}")
except:
    pass

print("\n" + "=" * 60)
print("✅ TEST COMPLETADO")
print("=" * 60)