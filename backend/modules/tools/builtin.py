# tools/builtin.py - Todas las tools del sistema registradas
import os
from .registry import ToolDef

def _get_weather(core=None, **kw):
    return core.get_weather() if core else "Weather no disponible"
def _get_time(core=None, **kw):
    return core.get_time() if core else __import__("datetime").datetime.now().strftime("%H:%M:%S")
def _get_tasks(core=None, **kw):
    return core.get_tasks() if core else "Tasks no disponible"
def _create_task(core=None, name="", **kw):
    return core.create_task(name) if core else "No disponible"
def _get_news(core=None, **kw):
    return core.get_news() if core else "News no disponible"
def _get_events(core=None, **kw):
    return core.get_events() if core else "Events no disponible"
def _search_vault(core=None, query="", **kw):
    return core.search_notes(query) if core else "Vault no disponible"
def _describe_scene(core=None, question="Que hay en la imagen?", **kw):
    return core._describe_scene(question) if core else "Vision no disponible"
def _privacy_status(core=None, **kw):
    return core._privacy_status() if core else "Privacy no disponible"
def _get_bitcoin(core=None, **kw):
    if core and hasattr(core, '_execute_tool'): return core._execute_tool("get_bitcoin", {})
    return "Bitcoin no disponible"
def _search_youtube(core=None, query="", **kw):
    if core and hasattr(core, '_execute_tool'): return core._execute_tool("search_youtube", {"query": query})
    return "YouTube no disponible"

ALL_TOOLS = [
    ToolDef("get_weather", "Obtiene el clima actual de una ciudad", {"type": "object", "properties": {"city": {"type": "string"}}, "required": []}, handler=_get_weather, capability="knowledge"),
    ToolDef("get_time", "Obtiene la hora y fecha actual", {"type": "object", "properties": {}}, handler=_get_time, capability="system"),
    ToolDef("get_tasks", "Lista tareas pendientes del usuario en Notion", {"type": "object", "properties": {}}, handler=_get_tasks, capability="knowledge"),
    ToolDef("create_task", "Crea una nueva tarea en Notion", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, handler=_create_task, capability="knowledge"),
    ToolDef("get_news", "Obtiene noticias actuales", {"type": "object", "properties": {"category": {"type": "string"}}}, handler=_get_news, capability="knowledge"),
    ToolDef("get_events", "Obtiene eventos del calendario de hoy", {"type": "object", "properties": {}}, handler=_get_events, capability="knowledge"),
    ToolDef("search_vault", "Busca en la boveda de conocimiento", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, handler=_search_vault, capability="knowledge"),
    ToolDef("describe_scene", "Captura y describe lo que ve la camara", {"type": "object", "properties": {"question": {"type": "string"}}}, handler=_describe_scene, capability="ambient"),
    ToolDef("privacy_status", "Muestra el estado de privacidad del sistema", {"type": "object", "properties": {}}, handler=_privacy_status, capability="ambient"),
    ToolDef("get_bitcoin", "Obtiene el precio actual de Bitcoin", {"type": "object", "properties": {}}, handler=_get_bitcoin, capability="knowledge"),
    ToolDef("search_youtube", "Busca videos en YouTube", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, handler=_search_youtube, capability="knowledge"),
]

def register_all(registry):
    for t in ALL_TOOLS:
        registry.register(t)
