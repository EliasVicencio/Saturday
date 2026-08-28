# agents/confirm.py - Human-in-the-loop para acciones destructivas
import time
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


DESTRUCTIVE_ACTIONS = {
    "kill_all_privacy": {"description": "Desactivar TODOS los sensores y permisos", "risk": "high"},
    "delete_memory": {"description": "Borrar memorias del usuario", "risk": "high"},
    "execute_command": {"description": "Ejecutar comando del sistema", "risk": "high"},
    "publish_event": {"description": "Publicar evento en el bus", "risk": "medium"},
    "send_message": {"description": "Enviar mensaje externo (WhatsApp/Telegram)", "risk": "medium"},
    "delete_file": {"description": "Eliminar un archivo", "risk": "high"},
}


@dataclass
class PendingConfirmation:
    id: str
    action: str
    description: str
    risk: str
    agent: str
    args: Dict[str, Any]
    timestamp: float
    expired: bool = False


class ConfirmationManager:
    def __init__(self, ttl_seconds: int = 300):
        self._pending: Dict[str, PendingConfirmation] = {}
        self._ttl = ttl_seconds

    def needs_confirmation(self, action: str) -> bool:
        return action in DESTRUCTIVE_ACTIONS

    def request_confirmation(self, action: str, agent: str, args: Dict = None) -> Optional[PendingConfirmation]:
        if action not in DESTRUCTIVE_ACTIONS:
            return None
        info = DESTRUCTIVE_ACTIONS[action]
        conf = PendingConfirmation(
            id=str(uuid.uuid4())[:8],
            action=action,
            description=info["description"],
            risk=info["risk"],
            agent=agent,
            args=args or {},
            timestamp=time.time(),
        )
        self._pending[conf.id] = conf
        return conf

    def confirm(self, confirmation_id: str) -> Optional[PendingConfirmation]:
        conf = self._pending.pop(confirmation_id, None)
        if conf and (time.time() - conf.timestamp) > self._ttl:
            conf.expired = True
            return None
        return conf

    def cancel(self, confirmation_id: str) -> bool:
        return self._pending.pop(confirmation_id, None) is not None

    def get_pending(self) -> list:
        now = time.time()
        expired = [k for k, v in self._pending.items() if (now - v.timestamp) > self._ttl]
        for k in expired:
            del self._pending[k]
        return [
            {
                "id": c.id,
                "action": c.action,
                "description": c.description,
                "risk": c.risk,
                "agent": c.agent,
                "args": c.args,
                "age_seconds": round(now - c.timestamp),
            }
            for c in self._pending.values()
        ]
