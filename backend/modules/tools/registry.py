# tools/registry.py - Registro central de herramientas de Saturday
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import time

@dataclass
class ToolDef:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable] = None
    destructive: bool = False
    capability: str = "general"
    def to_schema(self):
        return {"name": self.name, "description": self.description, "parameters": self.parameters}

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}
        self._log: List[Dict] = []
    def register(self, td: ToolDef):
        self._tools[td.name] = td
    def get(self, name):
        return self._tools.get(name)
    def execute(self, name, args=None, core=None):
        t = self._tools.get(name)
        if not t: return f"Tool desconocida: {name}"
        if not t.handler: return f"Tool {name} sin handler"
        args = args or {}
        start = time.time()
        result, error = None, None
        try:
            result = t.handler(core=core, **args) if core else t.handler(**args)
        except Exception as e:
            error = str(e)
            result = f"Error en {name}: {error}"
        dur = (time.time() - start) * 1000
        self._log.append({"tool": name, "args": args, "result": str(result)[:500], "duration_ms": round(dur, 2), "error": error, "timestamp": time.time()})
        return result
    def list_tools(self):
        return [t.to_schema() for t in self._tools.values()]
    def list_by_capability(self, cap):
        return [n for n, t in self._tools.items() if t.capability == cap]
    def get_log(self):
        return list(self._log)
    def get_schemas(self):
        return [t.to_schema() for t in self._tools.values()]
