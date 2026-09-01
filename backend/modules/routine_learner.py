"""Aprendizaje de rutinas del usuario."""
import json, os, logging
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Any

logger = logging.getLogger("saturday.routines")

class RoutineLearner:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._patterns_file = os.path.join(self.data_dir, 'routine_patterns.json')

    def _load_patterns(self) -> Dict:
        try:
            if os.path.exists(self._patterns_file):
                with open(self._patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"interactions": [], "patterns": {}}

    def _save_patterns(self, patterns: Dict):
        try:
            with open(self._patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando patrones: {e}")

    def record_interaction(self, intent: str):
        patterns = self._load_patterns()
        now = datetime.now()
        patterns["interactions"].append({
            "intent": intent,
            "hour": now.hour,
            "weekday": now.weekday(),
            "timestamp": now.isoformat()
        })
        patterns["interactions"] = patterns["interactions"][-500:]

        self._compute_patterns(patterns)
        self._save_patterns(patterns)

    def _compute_patterns(self, patterns: Dict):
        interactions = patterns.get("interactions", [])
        if len(interactions) < 5:
            patterns["patterns"] = {"status": "insufficient_data", "collected": len(interactions)}
            return

        by_hour = defaultdict(list)
        for i in interactions:
            by_hour[i["hour"]].append(i["intent"])

        hourly = {}
        for hour, intents in by_hour.items():
            counter = Counter(intents)
            top = counter.most_common(3)
            hourly[str(hour)] = [{"intent": t, "frequency": c} for t, c in top]

        by_weekday = defaultdict(list)
        for i in interactions:
            by_weekday[i["weekday"]].append(i["intent"])

        weekday_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        weekly = {}
        for wd, intents in by_weekday.items():
            counter = Counter(intents)
            top = counter.most_common(3)
            weekly[weekday_names[wd]] = [{"intent": t, "frequency": c} for t, c in top]

        patterns["patterns"] = {
            "hourly_routines": hourly,
            "weekly_routines": weekly,
            "total_samples": len(interactions),
            "status": "active" if len(interactions) >= 10 else "learning"
        }

    def get_routines(self) -> Dict[str, Any]:
        patterns = self._load_patterns()
        now = datetime.now()

        current_hour = str(now.hour)
        suggestions = []
        hourly = patterns.get("patterns", {}).get("hourly_routines", {})
        if current_hour in hourly:
            for item in hourly[current_hour]:
                if item["frequency"] >= 2:
                    suggestions.append(f"Normalmente haces '{item['intent']}' a esta hora")

        return {
            "status": patterns.get("patterns", {}).get("status", "insufficient_data"),
            "total_samples": patterns.get("patterns", {}).get("total_samples", 0),
            "current_suggestions": suggestions,
            "hourly_routines": hourly,
            "weekly_routines": patterns.get("patterns", {}).get("weekly_routines", {})
        }

    def get_status(self) -> str:
        data = self._load_patterns()
        status = data.get("patterns", {}).get("status", "insufficient_data")
        count = data.get("patterns", {}).get("total_samples", 0)
        emoji = "🔄" if status == "active" else "📈"
        return f"{emoji} Rutinas: {status} ({count} muestras)"
