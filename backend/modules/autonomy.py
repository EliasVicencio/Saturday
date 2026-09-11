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
    "proactive_notify": "ask",
    "calendar_read": "auto",
    "send_message": "ask",
    "memory_delete": "never",
    "system_command": "never",
    "privacy_control": "never",
}

# Tope de acciones autónomas por día, como red de seguridad contra loops
# o comportamiento inesperado, independiente del nivel configurado.
MAX_AUTONOMOUS_ACTIONS_PER_DAY = 50


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

    def _under_daily_cap(self) -> bool:
        today = date.today().isoformat()
        counter = self._state.get("action_count", {"date": "", "count": 0})
        if counter.get("date") != today:
            counter = {"date": today, "count": 0}
        if counter["count"] >= MAX_AUTONOMOUS_ACTIONS_PER_DAY:
            logger.warning(
                "Tope diario de %d acciones autónomas alcanzado, se frena hasta mañana",
                MAX_AUTONOMOUS_ACTIONS_PER_DAY,
            )
            return False
        counter["count"] += 1
        self._state["action_count"] = counter
        self._save()
        return True

    def allows(self, action: str) -> bool:
        """True si la acción puede ejecutarse sola, sin preguntar."""
        if self.paused:
            return False
        if self.get_level(action) != "auto":
            return False
        return self._under_daily_cap()

    def status(self) -> dict:
        today = date.today().isoformat()
        counter = self._state.get("action_count", {"date": "", "count": 0})
        used_today = counter["count"] if counter.get("date") == today else 0
        return {
            "paused": self.paused,
            "levels": dict(self._state.get("levels", DEFAULT_LEVELS)),
            "actions_today": used_today,
            "daily_cap": MAX_AUTONOMOUS_ACTIONS_PER_DAY,
        }
