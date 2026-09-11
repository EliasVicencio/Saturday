# api/auth.py - Authentication & Session Blueprint
from flask import Blueprint, request, jsonify
import hmac
import hashlib
import time
import os
import logging

logger = logging.getLogger('saturday.auth')

auth_bp = Blueprint('auth', __name__)

# These will be set by app.py after init
_api_key = ""
_session_tokens = {}
_session_secret = ""
_session_ttl = 3600

def init_auth(api_key, session_secret, session_ttl=3600):
    global _api_key, _session_tokens, _session_secret, _session_ttl
    _api_key = api_key
    _session_secret = session_secret
    _session_ttl = session_ttl

def _generate_session_token(ip):
    import base64
    expire = int(time.time()) + _session_ttl
    payload = f"{ip}|{expire}|{os.urandom(8).hex()}"
    sig = hmac.new(_session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()

def _is_valid_session(token):
    try:
        import base64
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        payload, sig = decoded.rsplit("|", 1)
        expected = hmac.new(_session_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        ip, expire_str, _ = payload.split("|", 2)
        return time.time() <= int(expire_str)
    except Exception:
        return False

def check_auth() -> bool:
    """Valida la request actual (header X-API-Key o sesion). No escribe respuesta."""
    if not _api_key:
        logger.warning("API key no configurada - rechazando request")
        return False
    key = request.headers.get("X-API-Key", "")
    if not key:
        return False
    if hmac.compare_digest(key, _api_key):
        return True
    return _is_valid_session(key)


def require_api_key(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if check_auth():
            return f(*args, **kwargs)
        logger.warning("API key invalida desde %s path=%s", request.remote_addr, request.path)
        return jsonify({"error": "Unauthorized"}), 401
    return decorated

@auth_bp.route('/api/auth/session', methods=['POST'])
def create_session():
    from flask_limiter import Limiter
    token = _generate_session_token(request.remote_addr)
    return jsonify({"token": token, "ttl": _session_ttl})
