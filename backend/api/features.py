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
