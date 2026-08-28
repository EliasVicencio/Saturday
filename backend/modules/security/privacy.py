# security/privacy.py - Switch de privacidad global
import json
import os
from typing import Dict

PRIVACY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "privacy.json")

class PrivacyManager:
    def __init__(self):
        self._state = {
            "camera_enabled": True,
            "microphone_enabled": True,
            "location_enabled": True,
            "ambient_sensors": True,
            "auto_save_images": False,
        }
        self._load()

    def _load(self):
        try:
            if os.path.exists(PRIVACY_FILE):
                with open(PRIVACY_FILE, "r") as f:
                    saved = json.load(f)
                self._state.update(saved)
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(PRIVACY_FILE), exist_ok=True)
            with open(PRIVACY_FILE, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception:
            pass

    def is_enabled(self, feature: str) -> bool:
        return self._state.get(feature, True)

    def set_enabled(self, feature: str, enabled: bool) -> bool:
        if feature not in self._state:
            return False
        self._state[feature] = enabled
        self._save()
        return True

    def kill_all(self) -> int:
        count = 0
        for key in list(self._state.keys()):
            if self._state[key] is True:
                self._state[key] = False
                count += 1
        self._save()
        return count

    def restore_all(self) -> int:
        count = 0
        for key in list(self._state.keys()):
            if self._state[key] is False:
                self._state[key] = True
                count += 1
        self._save()
        return count

    def get_state(self) -> Dict:
        return dict(self._state)

    def is_any_enabled(self) -> bool:
        return any(self._state.values())
