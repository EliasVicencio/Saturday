"""Análisis de productividad del usuario."""
import json, os, logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger("saturday.productivity")

class ProductivityTracker:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._metrics_file = os.path.join(self.data_dir, 'productivity_metrics.json')

    def _load_metrics(self) -> Dict:
        try:
            if os.path.exists(self._metrics_file):
                with open(self._metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"daily": {}, "sessions": 0, "total_interactions": 0}

    def _save_metrics(self, metrics: Dict):
        try:
            with open(self._metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando métricas: {e}")

    def record_interaction(self, intent: str):
        metrics = self._load_metrics()
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in metrics["daily"]:
            metrics["daily"][today] = {"interactions": 0, "intents": {}, "notes_created": 0, "reminders_created": 0, "tasks_completed": 0}

        day = metrics["daily"][today]
        day["interactions"] += 1
        day["intents"][intent] = day["intents"].get(intent, 0) + 1
        metrics["total_interactions"] += 1

        self._save_metrics(metrics)

    def get_daily_report(self) -> Dict[str, Any]:
        metrics = self._load_metrics()
        today = datetime.now().strftime("%Y-%m-%d")
        day_data = metrics.get("daily", {}).get(today, {"interactions": 0, "intents": {}})

        vault_notes = 0
        try:
            if self.core.vault:
                notes = self.core.vault.list_notes(layer="wiki")
                vault_notes = len(notes) if notes else 0
        except Exception:
            pass

        reminders = 0
        try:
            raw = self.core.data.get_reminders_today()
            if isinstance(raw, str) and raw.strip():
                reminders = len([l for l in raw.strip().split("\n") if l.strip()])
            elif isinstance(raw, list):
                reminders = len(raw)
        except Exception:
            pass

        tasks = 0
        try:
            if self.core.notion:
                tasks_list = self.core.notion.get_tasks()
                tasks = len(tasks_list) if tasks_list else 0
        except Exception:
            pass

        intents = day_data.get("intents", {})
        top_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)[:5]

        score = min(100, day_data.get("interactions", 0) * 5 + vault_notes * 2 + reminders * 3 + tasks * 10)

        return {
            "date": today,
            "interactions": day_data.get("interactions", 0),
            "vault_notes": vault_notes,
            "reminders": reminders,
            "pending_tasks": tasks,
            "top_intents": [{"intent": i, "count": c} for i, c in top_intents],
            "score": score,
            "total_all_time": metrics.get("total_interactions", 0)
        }

    def get_weekly_report(self) -> Dict[str, Any]:
        metrics = self._load_metrics()
        daily = metrics.get("daily", {})

        week_data = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day = daily.get(date, {"interactions": 0, "intents": {}})
            week_data.append({"date": date, "interactions": day.get("interactions", 0)})

        total = sum(d["interactions"] for d in week_data)
        avg = total / 7 if total > 0 else 0
        max_day = max(week_data, key=lambda x: x["interactions"]) if week_data else {"date": datetime.now().strftime("%Y-%m-%d"), "interactions": 0}

        return {
            "period": f"{week_data[0]['date']} al {week_data[-1]['date']}",
            "total_interactions": total,
            "daily_average": round(avg, 1),
            "most_productive_day": max_day,
            "daily_breakdown": week_data
        }

    def get_status(self) -> str:
        report = self.get_daily_report()
        return f"📊 Score hoy: {report['score']}/100 | {report['interactions']} interacciones | {report['vault_notes']} notas"
