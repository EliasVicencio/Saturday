# modules/autonomy.py - Kill switch y niveles de autonomía por acción
"""
Controla qué puede hacer Saturday por su cuenta, sin que el usuario pregunte.

Niveles por acción:
  - "auto":  se ejecuta sola (ideal para acciones de solo lectura: revisar
             correo, leer calendario, recolectar noticias).
  - "ask":   requiere confirmación humana antes de ejecutarse (acciones que
             salen hacia afuera: mandar un mensaje, publicar algo).
  - "never": nunca se ejecuta sola, pase lo que pase (borrar datos, comandos
             de sistema, acciones destructivas).

Además existe un "kill switch" global (`paused`): si está activo, NINGUNA
acción autónoma corre, sin importar su nivel individual.
"""
import json
import os
import logging
import threading
from datetime import datetime, date

logger = logging.getLogger("saturday.autonomy")

DEFAULT_LEVELS = {
    "email_check": "auto",
    "news_check": "auto",
    "data_organize": "auto",
    "daily_summary": "ask",
    "proactive_notify": "auto",
    "calendar_read": "auto",
    "send_message": "ask",
    "memory_delete": "never",
    "system_command": "never",
    "privacy_control": "never",
}

# Tope de acciones autónomas por día, como red de seguridad contra loops
# o comportamiento inesperado, independiente del nivel configurado.
MAX_AUTONOMOUS_ACTIONS_PER_DAY = 50

# Algunas acciones "salen hacia afuera" (te mandan un mensaje) y necesitan un
# tope más chico que el general, para que activar 'auto' no te sature de
# notificaciones aunque el nivel general lo permita.
ACTION_DAILY_CAPS = {
    "proactive_notify": 8,
}


class AutonomyManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._file = os.path.join(self.data_dir, 'autonomy_state.json')
        self._state = self._load()

    def _load(self) -> dict:
        try:
            if os.path.exists(self._file):
                with open(self._file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data.setdefault("paused", False)
                    data.setdefault("levels", dict(DEFAULT_LEVELS))
                    data.setdefault("action_count", {"date": "", "count": 0})
                    data.setdefault("action_counts", {})
                    return data
        except Exception as e:
            logger.error("Error cargando estado de autonomía: %s", e)
        return {"paused": False, "levels": dict(DEFAULT_LEVELS), "action_count": {"date": "", "count": 0}}

    def _save(self):
        try:
            with open(self._file, 'w', encoding='utf-8') as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Error guardando estado de autonomía: %s", e)

    @property
    def paused(self) -> bool:
        return self._state.get("paused", False)

    def pause(self):
        with self._lock:
            self._state["paused"] = True
            self._save()
        logger.warning("AUTONOMÍA PAUSADA — kill switch activado, ninguna tarea autónoma se ejecutará")

    def resume(self):
        with self._lock:
            self._state["paused"] = False
            self._save()
        logger.info("Autonomía reanudada")

    def get_level(self, action: str) -> str:
        return self._state.get("levels", {}).get(action, DEFAULT_LEVELS.get(action, "ask"))

    def set_level(self, action: str, level: str):
        if level not in ("auto", "ask", "never"):
            raise ValueError("Nivel inválido, debe ser 'auto', 'ask' o 'never'")
        with self._lock:
            self._state.setdefault("levels", dict(DEFAULT_LEVELS))
            self._state["levels"][action] = level
            self._save()
        logger.info("Nivel de autonomía de '%s' cambiado a '%s'", action, level)

    def _under_daily_cap(self, action: str) -> bool:
        today = date.today().isoformat()
        counters = self._state.setdefault("action_counts", {})
        counter = counters.get(action, {"date": "", "count": 0})
        if counter.get("date") != today:
            counter = {"date": today, "count": 0}

        # Cap global (todas las acciones autónomas combinadas)
        total = self._state.get("action_count", {"date": "", "count": 0})
        if total.get("date") != today:
            total = {"date": today, "count": 0}
        if total["count"] >= MAX_AUTONOMOUS_ACTIONS_PER_DAY:
            logger.warning(
                "Tope diario global de %d acciones autónomas alcanzado, se frena hasta mañana",
                MAX_AUTONOMOUS_ACTIONS_PER_DAY,
            )
            return False

        # Cap específico de la acción, si tiene uno definido (ej. notificaciones)
        specific_cap = ACTION_DAILY_CAPS.get(action)
        if specific_cap is not None and counter["count"] >= specific_cap:
            logger.info(
                "Tope diario de '%s' (%d) alcanzado, se frena hasta mañana", action, specific_cap
            )
            return False

        total["count"] += 1
        counter["count"] += 1
        self._state["action_count"] = total
        counters[action] = counter
        self._save()
        return True

    def allows(self, action: str) -> bool:
        """True si la acción puede ejecutarse sola, sin preguntar."""
        if self.paused:
            return False
        if self.get_level(action) != "auto":
            return False
        return self._under_daily_cap(action)

    def status(self) -> dict:
        today = date.today().isoformat()
        counter = self._state.get("action_count", {"date": "", "count": 0})
        used_today = counter["count"] if counter.get("date") == today else 0
        per_action_today = {
            action: c["count"]
            for action, c in self._state.get("action_counts", {}).items()
            if c.get("date") == today
        }
        return {
            "paused": self.paused,
            "levels": dict(self._state.get("levels", DEFAULT_LEVELS)),
            "actions_today": used_today,
            "daily_cap": MAX_AUTONOMOUS_ACTIONS_PER_DAY,
            "per_action_today": per_action_today,
            "per_action_caps": dict(ACTION_DAILY_CAPS),
        }
