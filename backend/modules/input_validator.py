# modules/input_validator.py - Validación centralizada de input
import re
from typing import Optional, Tuple

MAX_MESSAGE_LENGTH = 5000
MAX_TEXT_LENGTH = 10000
MAX_QUERY_LENGTH = 200
ALLOWED_AUDIO_EXTENSIONS = {'.webm', '.ogg', '.oga', '.wav', '.flac', '.mp3', '.m4a'}
MAX_AUDIO_SIZE_MB = 10
VALID_CATEGORIES = {'news', 'world', 'nation', 'business', 'technology', 'entertainment', 'sports', 'science', 'health'}
VALID_VAULT_LAYERS = {'raw', 'wiki', 'outputs'}
SAFE_PATH_CHARS = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')

def validate_message(text: str) -> Tuple[bool, Optional[str]]:
    if not text or not text.strip():
        return False, "Mensaje vacío"
    if len(text) > MAX_MESSAGE_LENGTH:
        return False, f"Mensaje demasiado largo (máx {MAX_MESSAGE_LENGTH} caracteres)"
    return True, None

def validate_text(text: str) -> Tuple[bool, Optional[str]]:
    if not text or not text.strip():
        return False, "Texto vacío"
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Texto demasiado largo (máx {MAX_TEXT_LENGTH} caracteres)"
    return True, None

def validate_search_query(q: str) -> Tuple[bool, Optional[str]]:
    if not q or not q.strip():
        return False, "Parámetro q requerido"
    if len(q) > MAX_QUERY_LENGTH:
        return False, f"Query demasiado largo (máx {MAX_QUERY_LENGTH} caracteres)"
    return True, None

def validate_category(category: Optional[str]) -> Tuple[bool, Optional[str]]:
    if category is None:
        return True, None
    if category.lower() not in VALID_CATEGORIES:
        return False, f"Categoría inválida. Válidas: {', '.join(sorted(VALID_CATEGORIES))}"
    return True, None

def validate_limit(limit_str: Optional[str], default: int = 8, max_val: int = 50) -> Tuple[bool, int, Optional[str]]:
    try:
        limit = int(limit_str) if limit_str else default
    except (ValueError, TypeError):
        return False, default, "Limit debe ser un número"
    if limit < 1:
        return False, default, "Limit debe ser >= 1"
    return True, min(limit, max_val), None

def validate_audio_file(filename: str, size_bytes: int) -> Tuple[bool, Optional[str]]:
    if not filename:
        return False, "Archivo vacío"
    import os
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Formato no soportado: {ext}"
    if size_bytes > MAX_AUDIO_SIZE_MB * 1024 * 1024:
        return False, f"Archivo demasiado grande (máx {MAX_AUDIO_SIZE_MB}MB)"
    return True, None

def validate_vault_path(path: str) -> Tuple[bool, Optional[str]]:
    if not path:
        return False, "Path requerido"
    if '..' in path:
        return False, "Path inválido (no se permite ..)"
    if path.startswith('/'):
        return False, "Path inválido (no debe empezar con /)"
    if not SAFE_PATH_CHARS.match(path):
        return False, "Path contiene caracteres no permitidos"
    return True, None

def validate_vault_layer(layer: Optional[str]) -> Tuple[bool, Optional[str]]:
    if layer is None:
        return True, None
    if layer not in VALID_VAULT_LAYERS:
        return False, f"Layer inválida. Válidas: {', '.join(sorted(VALID_VAULT_LAYERS))}"
    return True, None

def validate_note_input(data: dict) -> Tuple[bool, Optional[str]]:
    if not data:
        return False, "Body requerido"
    title = data.get('title', '').strip() if data.get('title') else ''
    content = data.get('content', '').strip() if data.get('content') else ''
    if not title and not content:
        return False, "Título o contenido requerido"
    if len(title) > 500:
        return False, "Título demasiado largo (máx 500)"
    if len(content) > 50000:
        return False, "Contenido demasiado largo (máx 50000)"
    return True, None