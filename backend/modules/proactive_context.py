"""Motor de contexto proactivo - sugiere acciones basadas en contexto."""
import json, os, logging
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger("saturday.proactive")

class ProactiveContext:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._history_file = os.path.join(self.data_dir, 'proactive_history.json')

    def _load_history(self) -> List[Dict]:
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_history(self, history: List[Dict]):
        try:
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(history[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando historial proactivo: {e}")

    def _get_time_context(self) -> Dict[str, Any]:
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        period = "mañana" if 5 <= hour < 12 else "tarde" if 12 <= hour < 18 else "noche" if 18 <= hour < 23 else "madrugada"
        is_weekend = weekday >= 5
        day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return {"hour": hour, "period": period, "weekday": day_names[weekday], "is_weekend": is_weekend, "date": now.strftime("%Y-%m-%d")}

    def get_context(self) -> Dict[str, Any]:
        time_ctx = self._get_time_context()
        context = {"time": time_ctx, "suggestions": [], "summary": ""}

        try:
            if self.core.calendar:
                events = self.core.calendar.get_today_events()
                if events:
                    context["upcoming_events"] = events[:3]
                    context["suggestions"].append({"type": "calendar", "text": f"Tienes {len(events)} evento(s) hoy", "priority": "high"})
        except Exception:
            pass

        try:
            weather = self.core.data.get_weather() if hasattr(self.core.data, 'get_weather') else None
            if weather:
                context["weather"] = weather
        except Exception:
            pass

        try:
            if self.core.vault:
                notes = self.core.vault.list_notes(layer="wiki")
                if notes and len(notes) > 0:
                    context["recent_notes"] = len(notes)
        except Exception:
            pass

        period = time_ctx["period"]
        hour = time_ctx["hour"]

        if period == "mañana" and not time_ctx["is_weekend"]:
            context["suggestions"].append({"type": "routine", "text": "Buenos días. ¿Quieres que revise tu agenda del día?", "priority": "medium"})
        elif period == "tarde" and hour == 14:
            context["suggestions"].append({"type": "routine", "text": "¿Quieres un resumen de lo que llevas del día?", "priority": "medium"})
        elif period == "noche":
            context["suggestions"].append({"type": "routine", "text": "¿Quieres que genere el resumen del día?", "priority": "medium"})

        parts = []
        parts.append(f"Es {time_ctx['period']} de {time_ctx['weekday']}")
        if context.get("upcoming_events"):
            parts.append(f"{len(context['upcoming_events'])} eventos pendientes")
        if context.get("weather"):
            w = context["weather"]
            if isinstance(w, dict):
                parts.append(f"clima: {w.get('condition', 'desconocido')}")
        context["summary"] = ", ".join(parts) if parts else "Sin contexto adicional"

        return context

    def record_interaction(self, intent: str, response: str):
        history = self._load_history()
        history.append({"timestamp": datetime.now().isoformat(), "intent": intent, "response_preview": response[:100] if response else ""})
        self._save_history(history)

    def get_suggestions(self) -> List[Dict[str, str]]:
        ctx = self.get_context()
        return ctx.get("suggestions", [])
