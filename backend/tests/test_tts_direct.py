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

print(f"ðŸ“‚ Project root: {project_root}")
print(f"ðŸ“‚ Backend dir: {backend_dir}")
print(f"ðŸ“‚ Modules dir: {modules_dir}")
print("-" * 50)

# ===== BUSCAR .env EN MÃšLTIPLES LUGARES =====
from dotenv import load_dotenv

# Posibles ubicaciones del .env
env_paths = [
    os.path.join(backend_dir, '.env'),      # backend/.env
    os.path.join(project_root, '.env'),     # Saturday/.env
    os.path.join(current_dir, '.env'),      # backend/tests/.env
]

env_loaded = False
for env_path in env_paths:
    print(f"ðŸ“„ Buscando .env en: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"âœ… .env encontrado y cargado desde: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    print("âŒ .env NO encontrado en ninguna ubicaciÃ³n")
    print("   Creando .env en backend/...")
    
    # Crear .env en backend
    env_path = os.path.join(backend_dir, '.env')
    with open(env_path, 'w') as f:
        f.write('GOOGLE_API_KEY=YOUR_API_KEY_HERE\n')
        f.write('SATURDAY_VOICE=es-ES-Chirp3-HD-Charon\n')
        f.write('SATURDAY_LANGUAGE=es-ES\n')
    print(f"âœ… .env creado en: {env_path}")
    load_dotenv(env_path)

print("-" * 50)

# Verificar que se cargÃ³ la API Key
import os
api_key = os.getenv("GOOGLE_API_KEY")
print(f"ðŸ”‘ GOOGLE_API_KEY: {api_key[:10] if api_key else 'NO'}...")

if not api_key:
    print("\nâŒ ERROR: GOOGLE_API_KEY no encontrada")
    print("   Agrega manualmente al archivo .env en backend/:")
    print("   GOOGLE_API_KEY=YOUR_API_KEY_HERE")
    sys.exit(1)

# ===== IMPORTAR =====
from modules.voice import VoiceManager

print("=" * 50)
print("ðŸ”Š PRUEBA DIRECTA DE GOOGLE TTS")
print("=" * 50)

voice = VoiceManager()
print(f"ðŸ”‘ API Key: {voice.api_key[:10] if voice.api_key else 'NO'}...")
print(f"ðŸŽ¤ Voz: {voice.voice_name}")
print("-" * 50)

text = "Hola, esto es una prueba de la voz de Google Charon"
print(f"ðŸ“ Texto: {text}")
print("ðŸŽ¤ Generando audio...")

audio_data = voice._synthesize_google_tts(text)

if audio_data:
    print(f"âœ… Audio generado: {len(audio_data)} bytes")
    audio_path = os.path.join(current_dir, "test_audio.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_data)
    print(f"ðŸ“ Audio guardado como: {audio_path}")
    print("â–¶ï¸ Reproduciendo...")
    os.system(f"start {audio_path}")
else:
    print("âŒ No se generÃ³ audio")
