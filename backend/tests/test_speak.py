# test_speak.py
import requests
import base64
import os

url = "http://localhost:5000/api/speak"
payload = {"text": "Hola, soy Saturday con voz de Google Charon"}

response = requests.post(url, json=payload)
data = response.json()

if data.get('audio'):
    print("✅ Audio generado correctamente")
    # Guardar el audio
    audio_bytes = base64.b64decode(data['audio'])
    with open("test_audio.mp3", "wb") as f:
        f.write(audio_bytes)
    print("📁 Audio guardado como test_audio.mp3")
    # Reproducir en Windows
    os.system("start test_audio.mp3")
else:
    print(f"❌ Error: {data}")