# backend/tests/test_speak.py
import os
import sys
import base64

# ===== CONFIGURAR PATH =====
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

import requests

print("=" * 50)
print("🔊 PRUEBA DEL ENDPOINT /api/speak")
print("=" * 50)

# Verificar que el backend esté corriendo
try:
    status_response = requests.get("http://localhost:5000/api/status", timeout=3)
    print(f"✅ Backend corriendo (status: {status_response.status_code})")
except:
    print("❌ El backend no está corriendo. Ejecuta: python backend/app.py")
    sys.exit(1)

url = "http://localhost:5000/api/speak"
payload = {"text": "Hola, soy Saturday con la voz de Google Charon"}

print(f"📤 Enviando a: {url}")
print(f"📝 Texto: {payload['text']}")

try:
    response = requests.post(url, json=payload, timeout=15)
    print(f"📊 Código: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('audio'):
            print("✅ Audio generado correctamente")
            
            # Guardar audio
            audio_bytes = base64.b64decode(data['audio'])
            audio_path = os.path.join(current_dir, "test_speak_audio.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            print(f"📁 Audio guardado como: {audio_path}")
            
            # Reproducir
            print("▶️ Reproduciendo...")
            os.system(f"start {audio_path}")
        else:
            print(f"❌ Error: {data}")
    else:
        print(f"❌ Error: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Error: No se pudo conectar al servidor. ¿Está corriendo el backend?")
except Exception as e:
    print(f"❌ Error: {e}")