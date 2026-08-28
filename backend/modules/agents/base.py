# agents/base.py - Clase base para todos los agentes de Saturday
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable


@dataclass
class AgentResult:
    response: str
    agent: str
    tools_called: List[Dict[str, Any]] = field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_action: str = ""
    confirmation_data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0
    checkpoint_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "agent": self.agent,
            "tools_called": self.tools_called,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_action": self.confirmation_action,
            "confirmation_data": self.confirmation_data,
            "duration_ms": self.duration_ms,
            "checkpoint_id": self.checkpoint_id,
        }


class BaseAgent:
    """Clase base para agentes. Cada capability extiende esta clase."""

    name: str = "base"
    description: str = ""
    tools: List[str] = []
    destructive_actions: List[str] = []

    def __init__(self, core=None):
        self.core = core
        self._tool_log: List[Dict[str, Any]] = []

    def can_handle(self, text: str) -> float:
        """Retorna un score de 0-1 de cuan bien este agente maneja el texto."""
        return 0.0

    def process(self, text: str, chat_id: int = None, context: Dict = None) -> AgentResult:
        """Procesa el mensaje. Debe ser sobreescrito por cada agente."""
        raise NotImplementedError

    def call_tool(self, tool_name: str, args: Dict[str, Any] = None) -> Any:
        """Ejecuta una tool registrada en core y la loggea."""
        start = time.time()
        args = args or {}
        result = None
        error = None

        try:
            if self.core and hasattr(self.core, '_execute_tool'):
                result = self.core._execute_tool(tool_name, args)
            else:
                result = f"Tool {tool_name} no disponible (core no inicializado)"
        except Exception as e:
            error = str(e)
            result = f"Error en {tool_name}: {error}"

        duration = (time.time() - start) * 1000
        log_entry = {
            "tool": tool_name,
            "args": args,
            "result": str(result)[:500],
            "duration_ms": round(duration, 2),
            "error": error,
            "timestamp": time.time(),
        }
        self._tool_log.append(log_entry)
        return result

    def is_destructive(self, action: str) -> bool:
        """Verifica si una acción requiere confirmación."""
        return action in self.destructive_actions

    def get_system_prompt(self) -> str:
        """Prompt del sistema para este agente. Override en subclases."""
        return f"Sos {self.name}. {self.description}"

    def get_tool_log(self) -> List[Dict]:
        return list(self._tool_log)

    def clear_tool_log(self):
        self._tool_log.clear()
