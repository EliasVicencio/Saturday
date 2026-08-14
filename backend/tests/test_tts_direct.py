# backend/tests/test_tts_direct.py
import os
import sys

# ===== CONFIGURAR PATH =====
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
modules_dir = os.path.join(backend_dir, 'modules')

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

print(f"📂 Project root: {project_root}")
print(f"📂 Backend dir: {backend_dir}")
print(f"📂 Modules dir: {modules_dir}")
print("-" * 50)

# ===== BUSCAR .env EN MÚLTIPLES LUGARES =====
from dotenv import load_dotenv

# Posibles ubicaciones del .env
env_paths = [
    os.path.join(backend_dir, '.env'),      # backend/.env
    os.path.join(project_root, '.env'),     # Saturday/.env
    os.path.join(current_dir, '.env'),      # backend/tests/.env
]

env_loaded = False
for env_path in env_paths:
    print(f"📄 Buscando .env en: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ .env encontrado y cargado desde: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("❌ .env NO encontrado en ninguna ubicación")
    print("   Creando .env en backend/...")
    
    # Crear .env en backend
    env_path = os.path.join(backend_dir, '.env')
    with open(env_path, 'w') as f:
        f.write('GOOGLE_API_KEY=AIzaSyCGt-YK7pzrCdgI3rWmoQpXVsXQm-C2BnE\n')
        f.write('SATURDAY_VOICE=es-ES-Chirp3-HD-Charon\n')
        f.write('SATURDAY_LANGUAGE=es-ES\n')
    print(f"✅ .env creado en: {env_path}")
    load_dotenv(env_path)

print("-" * 50)

# Verificar que se cargó la API Key
import os
api_key = os.getenv("GOOGLE_API_KEY")
print(f"🔑 GOOGLE_API_KEY: {api_key[:10] if api_key else 'NO'}...")

if not api_key:
    print("\n❌ ERROR: GOOGLE_API_KEY no encontrada")
    print("   Agrega manualmente al archivo .env en backend/:")
    print("   GOOGLE_API_KEY=AIzaSyCGt-YK7pzrCdgI3rWmoQpXVsXQm-C2BnE")
    sys.exit(1)

# ===== IMPORTAR =====
from modules.voice import VoiceManager

print("=" * 50)
print("🔊 PRUEBA DIRECTA DE GOOGLE TTS")
print("=" * 50)

voice = VoiceManager()
print(f"🔑 API Key: {voice.api_key[:10] if voice.api_key else 'NO'}...")
print(f"🎤 Voz: {voice.voice_name}")
print("-" * 50)

text = "Hola, esto es una prueba de la voz de Google Charon"
print(f"📝 Texto: {text}")
print("🎤 Generando audio...")

audio_data = voice._synthesize_google_tts(text)

if audio_data:
    print(f"✅ Audio generado: {len(audio_data)} bytes")
    audio_path = os.path.join(current_dir, "test_audio.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_data)
    print(f"📁 Audio guardado como: {audio_path}")
    print("▶️ Reproduciendo...")
    os.system(f"start {audio_path}")
else:
    print("❌ No se generó audio")