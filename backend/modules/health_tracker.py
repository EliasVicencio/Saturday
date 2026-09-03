"""Seguimiento de salud automatico desde Google Fit."""
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
        self._goals = {
            "steps": 10000,
            "calories": 2000,
            "distance_km": 8,
            "heart_rate_max": 100,
            "heart_rate_min": 60
        }

    def _load_data(self) -> Dict:
        try:
            if os.path.exists(self._health_file):
                with open(self._health_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"daily": {}, "goals": self._goals}

    def _save_data(self, data: Dict):
        try:
            with open(self._health_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando datos de salud: {e}")

    def sync_from_google_fit(self) -> Dict[str, Any]:
        """Sincroniza datos automaticamente desde Google Fit"""
        if not self.core.google_fit or not self.core.google_fit.is_connected():
            return {"synced": False, "error": "Google Fit no conectado"}
        
        try:
            fit_data = self.core.google_fit.get_today_data()
            
            if not fit_data.get("connected"):
                return {"synced": False, "error": "Google Fit no conectado"}
            
            today = datetime.now().strftime("%Y-%m-%d")
            data = self._load_data()
            
            if "daily" not in data:
                data["daily"] = {}
            
            data["daily"][today] = {
                "date": today,
                "synced_at": datetime.now().isoformat(),
                "steps": fit_data.get("steps", 0),
                "calories": fit_data.get("calories", 0),
                "distance_km": fit_data.get("distance_km", 0),
                "heart_rate_avg": fit_data.get("heart_rate_avg"),
            }
            
            # Guardar historial (ultimos 30 dias)
            dates = sorted(data["daily"].keys())
            if len(dates) > 30:
                for old_date in dates[:-30]:
                    del data["daily"][old_date]
            
            self._save_data(data)
            
            logger.info(f"Google Fit sincronizado: {fit_data.get('steps', 0)} pasos")
            return {"synced": True, "data": data["daily"][today]}
            
        except Exception as e:
            logger.error(f"Error sincronizando Google Fit: {e}")
            return {"synced": False, "error": str(e)}

    def get_today(self) -> Dict[str, Any]:
        """Obtiene datos de hoy (auto-sync si esta conectado)"""
        # Auto-sync si Google Fit esta conectado
        if self.core.google_fit and self.core.google_fit.is_connected():
            self.sync_from_google_fit()
        
        data = self._load_data()
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = data.get("daily", {}).get(today, {})
        
        if not today_data:
            return {
                "date": today,
                "connected": self.core.google_fit.is_connected() if self.core.google_fit else False,
                "data": None,
                "message": "No hay datos de salud para hoy"
            }
        
        goals = data.get("goals", self._goals)
        analysis = self._analyze_today(today_data, goals)
        
        return {
            "date": today,
            "connected": True,
            "data": today_data,
            "analysis": analysis,
            "goals": goals
        }

    def _analyze_today(self, data: Dict, goals: Dict) -> Dict[str, Any]:
        """Analiza datos de hoy vs metas"""
        steps = data.get("steps", 0)
        calories = data.get("calories", 0)
        distance = data.get("distance_km", 0)
        heart_rate = data.get("heart_rate_avg")
        
        steps_pct = round((steps / goals.get("steps", 10000)) * 100) if goals.get("steps") else 0
        calories_pct = round((calories / goals.get("calories", 2000)) * 100) if goals.get("calories") else 0
        distance_pct = round((distance / goals.get("distance_km", 8)) * 100) if goals.get("distance_km") else 0
        
        return {
            "steps": {"value": steps, "goal": goals.get("steps", 10000), "pct": steps_pct},
            "calories": {"value": calories, "goal": goals.get("calories", 2000), "pct": calories_pct},
            "distance_km": {"value": distance, "goal": goals.get("distance_km", 8), "pct": distance_pct},
            "heart_rate_avg": heart_rate,
        }

    def get_weekly(self) -> Dict[str, Any]:
        """Obtiene datos de la ultima semana"""
        data = self._load_data()
        daily = data.get("daily", {})
        
        week_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in daily:
                week_data.append(daily[date])
        
        if not week_data:
            return {"period": "sin datos", "data": []}
        
        avg_steps = sum(d.get("steps", 0) for d in week_data) / len(week_data)
        avg_calories = sum(d.get("calories", 0) for d in week_data) / len(week_data)
        total_distance = sum(d.get("distance_km", 0) for d in week_data)
        
        return {
            "period": f"{(datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')} al {datetime.now().strftime('%Y-%m-%d')}",
            "days": len(week_data),
            "avg_steps": round(avg_steps),
            "avg_calories": round(avg_calories),
            "total_distance_km": round(total_distance, 2),
            "daily": week_data
        }

    def set_goal(self, category: str, value: float) -> str:
        data = self._load_data()
        if "goals" not in data:
            data["goals"] = self._goals
        data["goals"][category] = value
        self._save_data(data)
        return f"Meta actualizada: {category} = {value}"

    def get_status(self) -> str:
        today = self.get_today()
        if not today.get("data"):
            return "Sin datos de salud hoy"
        
        data = today["data"]
        return f"Pasos: {data.get('steps', 0)} | Calorias: {data.get('calories', 0)} | Distancia: {data.get('distance_km', 0)} km"