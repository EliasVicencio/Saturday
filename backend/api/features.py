"""Blueprint para las 5 nuevas features: contexto, emails, productividad, rutinas, salud."""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger("saturday.features")
features_bp = Blueprint('features', __name__)
_core = None

def init_features(saturday):
    global _core
    _core = saturday

# --- Proactive Context ---
@features_bp.route("/api/proactive/context", methods=["GET"])
def get_proactive_context():
    if not _core or not hasattr(_core, 'proactive') or not _core.proactive:
        return jsonify({"error": "Contexto proactivo no disponible"}), 503
    try:
        context = _core.proactive.get_context()
        return jsonify(context)
    except Exception as e:
        logger.error(f"Error contexto proactivo: {e}")
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/proactive/suggestions", methods=["GET"])
def get_proactive_suggestions():
    if not _core or not hasattr(_core, 'proactive') or not _core.proactive:
        return jsonify({"suggestions": []})
    try:
        suggestions = _core.proactive.get_suggestions()
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        return jsonify({"suggestions": [], "error": str(e)})

# --- Email Summary ---
@features_bp.route("/api/emails/summary", methods=["GET"])
def get_email_summary():
    if not _core or not hasattr(_core, 'email_summary') or not _core.email_summary:
        return jsonify({"error": "Resumen de correos no disponible"}), 503
    try:
        summary = _core.email_summary.get_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error resumen emails: {e}")
        return jsonify({"error": str(e)}), 500

# --- Productivity ---
@features_bp.route("/api/productivity/daily", methods=["GET"])
def get_productivity_daily():
    if not _core or not hasattr(_core, 'productivity') or not _core.productivity:
        return jsonify({"error": "Productividad no disponible"}), 503
    try:
        report = _core.productivity.get_daily_report()
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error productividad: {e}")
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/productivity/weekly", methods=["GET"])
def get_productivity_weekly():
    if not _core or not hasattr(_core, 'productivity') or not _core.productivity:
        return jsonify({"error": "Productividad no disponible"}), 503
    try:
        report = _core.productivity.get_weekly_report()
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error productividad semanal: {e}")
        return jsonify({"error": str(e)}), 500

# --- Routines ---
@features_bp.route("/api/routines", methods=["GET"])
def get_routines():
    if not _core or not hasattr(_core, 'routines') or not _core.routines:
        return jsonify({"error": "Aprendizaje de rutinas no disponible"}), 503
    try:
        routines = _core.routines.get_routines()
        return jsonify(routines)
    except Exception as e:
        logger.error(f"Error rutinas: {e}")
        return jsonify({"error": str(e)}), 500

# --- Health ---
@features_bp.route("/api/health/today", methods=["GET"])
def get_health_today():
    if not _core or not hasattr(_core, 'health') or not _core.health:
        return jsonify({"error": "Salud no disponible"}), 503
    try:
        today = _core.health.get_today()
        return jsonify(today)
    except Exception as e:
        logger.error(f"Error salud hoy: {e}")
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/weekly", methods=["GET"])
def get_health_weekly():
    if not _core or not hasattr(_core, 'health') or not _core.health:
        return jsonify({"error": "Salud no disponible"}), 503
    try:
        weekly = _core.health.get_weekly()
        return jsonify(weekly)
    except Exception as e:
        logger.error(f"Error salud semanal: {e}")
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/log", methods=["POST"])
def log_health():
    if not _core or not hasattr(_core, 'health') or not _core.health:
        return jsonify({"error": "Salud no disponible"}), 503
    try:
        data = request.get_json(silent=True) or {}
        category = data.get("category", "").strip()
        value = data.get("value", "")
        note = data.get("note", "")
        if not category or not value:
            return jsonify({"error": "Se requiere category y value"}), 400
        result = _core.health.log_entry(category, value, note)
        return jsonify({"message": result})
    except Exception as e:
        logger.error(f"Error registrando salud: {e}")
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/goal", methods=["POST"])
def set_health_goal():
    if not _core or not hasattr(_core, 'health') or not _core.health:
        return jsonify({"error": "Salud no disponible"}), 503
    try:
        data = request.get_json(silent=True) or {}
        category = data.get("category", "").strip()
        value = data.get("value")
        if not category or value is None:
            return jsonify({"error": "Se requiere category y value"}), 400
        result = _core.health.set_goal(category, float(value))
        return jsonify({"message": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Google Fit ---
GOOGLE_FIT_REDIRECT = "https://saturday.viewdns.net/api/health/google-fit/callback"

@features_bp.route("/api/health/google-fit/auth-url", methods=["GET"])
def google_fit_auth_url():
    if not _core or not hasattr(_core, 'google_fit') or not _core.google_fit:
        return jsonify({"error": "Google Fit no disponible"}), 503
    try:
        url = _core.google_fit.get_auth_url(redirect_uri=GOOGLE_FIT_REDIRECT)
        if url:
            return jsonify({"auth_url": url, "instructions": "Abre esta URL en tu navegador, autoriza, y copia el codigo que te den. Luego envia el codigo via POST a /api/health/google-fit/callback con {code: tu_codigo}"})
        return jsonify({"error": "Credenciales no configuradas"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/google-fit/callback", methods=["GET", "POST"])
def google_fit_callback():
    if not _core or not hasattr(_core, 'google_fit') or not _core.google_fit:
        return jsonify({"error": "Google Fit no disponible"}), 503
    try:
        code = request.args.get("code", "") if request.method == "GET" else ""
        if not code:
            data = request.get_json(silent=True) or {}
            code = data.get("code", "")
        if not code:
            return jsonify({"error": "Se requiere el campo code"}), 400
        success = _core.google_fit.exchange_code(code, GOOGLE_FIT_REDIRECT)
        if success:
            if request.method == "GET":
                return '<html><body style="background:#0a0a14;color:#4caf50;font-family:sans-serif;text-align:center;padding-top:100px"><h1>Google Fit conectado!</h1><p>Puedes cerrar esta ventana.</p></body></html>'
            return jsonify({"message": "Google Fit conectado exitosamente"})
        return jsonify({"error": "Error procesando el codigo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/google-fit/data", methods=["GET"])
def google_fit_data():
    if not _core or not hasattr(_core, 'google_fit') or not _core.google_fit:
        return jsonify({"error": "Google Fit no disponible"}), 503
    try:
        data = _core.google_fit.get_today_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/health/google-fit/status", methods=["GET"])
def google_fit_status():
    if not _core or not hasattr(_core, 'google_fit') or not _core.google_fit:
        return jsonify({"connected": False, "error": "Google Fit no disponible"})
    try:
        return jsonify({"connected": _core.google_fit.is_connected()})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})

# --- Gmail ---
GMAIL_REDIRECT = "https://saturday.viewdns.net/api/gmail/callback"

@features_bp.route("/api/gmail/auth-url", methods=["GET"])
def gmail_auth_url():
    if not _core or not hasattr(_core, 'gmail') or not _core.gmail:
        return jsonify({"error": "Gmail no disponible"}), 503
    try:
        url = _core.gmail.get_auth_url(redirect_uri=GMAIL_REDIRECT)
        if url:
            return jsonify({"auth_url": url})
        return jsonify({"error": "Credenciales no configuradas"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/gmail/callback", methods=["GET", "POST"])
def gmail_callback():
    if not _core or not hasattr(_core, 'gmail') or not _core.gmail:
        return jsonify({"error": "Gmail no disponible"}), 503
    try:
        code = request.args.get("code", "") if request.method == "GET" else ""
        if not code:
            data = request.get_json(silent=True) or {}
            code = data.get("code", "")
        if not code:
            return jsonify({"error": "Se requiere el campo code"}), 400
        success = _core.gmail.exchange_code(code, GMAIL_REDIRECT)
        if success:
            if request.method == "GET":
                return '<html><body style="background:#0a0a14;color:#4caf50;font-family:sans-serif;text-align:center;padding-top:100px"><h1>Gmail conectado!</h1><p>Puedes cerrar esta ventana.</p></body></html>'
            return jsonify({"message": "Gmail conectado exitosamente"})
        return jsonify({"error": "Error procesando codigo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/gmail/status", methods=["GET"])
def gmail_status():
    if not _core or not hasattr(_core, 'gmail') or not _core.gmail:
        return jsonify({"connected": False, "error": "Gmail no disponible"})
    try:
        return jsonify({"connected": _core.gmail.is_connected()})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})

@features_bp.route("/api/gmail/emails", methods=["GET"])
def gmail_emails():
    if not _core or not hasattr(_core, 'gmail') or not _core.gmail:
        return jsonify({"error": "Gmail no disponible"}), 503
    try:
        query = request.args.get("q", "")
        max_results = int(request.args.get("limit", 10))
        emails = _core.gmail.get_recent_emails(max_results=max_results, query=query)
        return jsonify({"emails": emails, "count": len(emails)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@features_bp.route("/api/gmail/summary", methods=["GET"])
def gmail_summary():
    if not _core or not hasattr(_core, 'gmail') or not _core.gmail:
        return jsonify({"error": "Gmail no disponible"}), 503
    try:
        summary = _core.gmail.get_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ Google Drive Endpoints ============
@features_bp.route("/api/google-drive/auth-url", methods=["GET"])
def google_drive_auth_url():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    url = _core.google_drive.get_auth_url()
    return jsonify({"auth_url": url})

@features_bp.route("/api/google-drive/callback", methods=["GET"])
def google_drive_callback():
    code = request.args.get("code")
    if not code:
        return redirect("https://saturday.viewdns.net?google_drive=error")
    
    if _core and hasattr(_core, 'google_drive') and _core.google_drive:
        success = _core.google_drive.exchange_code(code)
        if success:
            return redirect("https://saturday.viewdns.net?google_drive=success")
    
    return redirect("https://saturday.viewdns.net?google_drive=error")

@features_bp.route("/api/google-drive/status", methods=["GET"])
def google_drive_status():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"connected": False})
    return jsonify({"connected": _core.google_drive.is_connected()})

@features_bp.route("/api/google-drive/files", methods=["GET"])
def google_drive_files():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    
    folder_id = request.args.get("folder_id")
    query = request.args.get("query")
    max_results = int(request.args.get("max_results", 20))
    
    files = _core.google_drive.list_files(folder_id=folder_id, query=query, max_results=max_results)
    return jsonify({"files": files, "count": len(files)})

@features_bp.route("/api/google-drive/search", methods=["GET"])
def google_drive_search():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query requerido"}), 400
    
    files = _core.google_drive.search_files(query)
    return jsonify({"files": files, "count": len(files)})

@features_bp.route("/api/google-drive/file/<file_id>", methods=["GET"])
def google_drive_file(file_id):
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    
    content = _core.google_drive.get_file_content(file_id)
    return jsonify({"content": content})

@features_bp.route("/api/google-drive/create", methods=["POST"])
def google_drive_create():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    
    data = request.get_json() or {}
    name = data.get("name")
    content = data.get("content", "")
    folder_id = data.get("folder_id")
    
    if not name:
        return jsonify({"error": "Nombre requerido"}), 400
    
    result = _core.google_drive.create_file(name, content, folder_id)
    return jsonify({"success": result is not None, "file": result})

@features_bp.route("/api/google-drive/storage", methods=["GET"])
def google_drive_storage():
    if not _core or not hasattr(_core, 'google_drive') or not _core.google_drive:
        return jsonify({"error": "Google Drive no disponible"}), 500
    
    info = _core.google_drive.get_storage_info()
    return jsonify(info)
