"""Seguimiento de salud y bienestar."""
import json, os, logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger("saturday.health")

class HealthTracker:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._health_file = os.path.join(self.data_dir, 'health_data.json')

    def _load_data(self) -> Dict:
        try:
            if os.path.exists(self._health_file):
                with open(self._health_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"entries": [], "goals": {"water": 8, "exercise": 30, "sleep": 8}}

    def _save_data(self, data: Dict):
        try:
            with open(self._health_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando datos de salud: {e}")

    def log_entry(self, category: str, value: Any, note: str = "") -> str:
        data = self._load_data()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": category,
            "value": value,
            "note": note
        }
        data["entries"].append(entry)
        data["entries"] = data["entries"][-200:]
        self._save_data(data)

        labels = {"mood": "estado de ánimo", "sleep": "sueño", "exercise": "ejercicio", "water": "agua", "weight": "peso", "note": "nota"}
        label = labels.get(category, category)
        return f"✅ Registrado: {label} = {value}" + (f" ({note})" if note else "")

    def get_today(self) -> Dict[str, Any]:
        data = self._load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [e for e in data.get("entries", []) if e.get("date") == today]

        categories = {}
        for e in entries:
            cat = e["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(e)

        goals = data.get("goals", {})
        compliance = {}

        if "water" in categories:
            total_water = sum(1 for e in categories["water"])
            compliance["water"] = {"current": total_water, "goal": goals.get("water", 8), "met": total_water >= goals.get("water", 8)}
        if "exercise" in categories:
            total_exercise = sum(float(e["value"]) for e in categories["exercise"] if str(e["value"]).replace(".", "").isdigit())
            compliance["exercise"] = {"current": total_exercise, "goal": goals.get("exercise", 30), "met": total_exercise >= goals.get("exercise", 30)}
        if "sleep" in categories:
            last_sleep = categories["sleep"][-1]["value"]
            compliance["sleep"] = {"current": last_sleep, "goal": goals.get("sleep", 8), "met": float(last_sleep) >= goals.get("sleep", 8)}

        mood_entries = categories.get("mood", [])
        mood_avg = None
        if mood_entries:
            try:
                mood_values = [float(e["value"]) for e in mood_entries if str(e["value"]).replace(".", "").isdigit()]
                mood_avg = round(sum(mood_values) / len(mood_values), 1) if mood_values else None
            except Exception:
                pass

        return {
            "date": today,
            "entries": entries,
            "compliance": compliance,
            "mood_average": mood_avg,
            "total_entries": len(entries)
        }

    def get_weekly(self) -> Dict[str, Any]:
        data = self._load_data()
        entries = data.get("entries", [])

        week_entries = []
        for e in entries:
            try:
                entry_date = datetime.fromisoformat(e["timestamp"]).date()
                if (datetime.now().date() - entry_date).days < 7:
                    week_entries.append(e)
            except Exception:
                pass

        by_date = {}
        for e in week_entries:
            d = e.get("date", "")
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(e)

        goals = data.get("goals", {})
        daily_compliance = []
        for d, day_entries in sorted(by_date.items()):
            cats = {}
            for e in day_entries:
                cats[e["category"]] = e
            met = 0
            total = 0
            if "water" in goals:
                total += 1
                if sum(1 for e in day_entries if e["category"] == "water") >= goals["water"]:
                    met += 1
            if "exercise" in goals:
                total += 1
                if sum(float(e["value"]) for e in day_entries if e["category"] == "exercise" and str(e["value"]).replace(".", "").isdigit()) >= goals["exercise"]:
                    met += 1
            daily_compliance.append({"date": d, "met": met, "total": total, "percentage": round(met / total * 100) if total > 0 else 0})

        avg_compliance = sum(d["percentage"] for d in daily_compliance) / len(daily_compliance) if daily_compliance else 0

        return {
            "period": f"{(datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')} al {datetime.now().strftime('%Y-%m-%d')}",
            "total_entries": len(week_entries),
            "avg_compliance": round(avg_compliance),
            "daily_breakdown": daily_compliance
        }

    def set_goal(self, category: str, value: float) -> str:
        data = self._load_data()
        if "goals" not in data:
            data["goals"] = {}
        data["goals"][category] = value
        self._save_data(data)
        return f"🎯 Meta actualizada: {category} = {value}"

    def get_status(self) -> str:
        today = self.get_today()
        compliance = today.get("compliance", {})
        met = sum(1 for v in compliance.values() if v.get("met"))
        total = len(compliance)
        return f"❤️ Salud hoy: {met}/{total} metas alcanzadas | {today['total_entries']} registros"
