# backend/tests/check_imports.py
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
modules_dir = os.path.join(backend_dir, 'modules')

print("🔍 VERIFICANDO IMPORTACIONES")
print("=" * 50)

print(f"📂 Project root: {project_root}")
print(f"📂 Backend dir: {backend_dir}")
print(f"📂 Modules dir: {modules_dir}")
print(f"📂 modules existe: {os.path.exists(modules_dir)}")
print(f"📂 voice.py existe: {os.path.exists(os.path.join(modules_dir, 'voice.py'))}")

# Agregar al path
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

print("-" * 50)

try:
    import modules
    print(f"✅ modules importado: {modules.__file__}")
except ImportError as e:
    print(f"❌ modules no importado: {e}")

try:
    from modules import voice
    print(f"✅ modules.voice importado")
except ImportError as e:
    print(f"❌ modules.voice no importado: {e}")

try:
    from modules.voice import VoiceManager
    print(f"✅ VoiceManager importado correctamente")
except ImportError as e:
    print(f"❌ VoiceManager no importado: {e}")