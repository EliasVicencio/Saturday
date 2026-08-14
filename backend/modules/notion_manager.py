# modules/notion_manager.py
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional

class NotionManager:
    """Gestor de tareas con Notion - Versión MVP"""
    
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
        
        # Verificar conexión
        try:
            response = requests.post(
                f"{self.base_url}/databases/{self.database_id}/query",
                headers=self.headers,
                json={"page_size": 1}
            )
            if response.status_code == 200:
                print("✅ Notion conectado correctamente")
            else:
                print(f"⚠️ Error conectando a Notion: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error conectando a Notion: {e}")
    
    # ============ OBTENER TAREAS ============
    
    def get_tasks(self, status: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Obtiene tareas de Notion"""
        try:
            url = f"{self.base_url}/databases/{self.database_id}/query"
            payload = {"page_size": limit}
            
            if status == "Todo":
                payload["filter"] = {
                    "property": "Hecho",
                    "checkbox": {"equals": False}
                }
            elif status == "Completado":
                payload["filter"] = {
                    "property": "Hecho",
                    "checkbox": {"equals": True}
                }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            tasks = []
            for page in data.get("results", []):
                task = self._parse_task(page)
                if task:
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error obteniendo tareas: {e}")
            return []
    
    def _parse_task(self, page: Dict) -> Optional[Dict]:
        """Parsea una tarea de Notion"""
        try:
            props = page.get("properties", {})
            
            # Obtener nombre
            name = "Sin título"
            if "Nombre" in props:
                title_items = props["Nombre"].get("title", [])
                if title_items:
                    name = title_items[0].get("text", {}).get("content", "Sin título")
            
            # Obtener estado
            estado = "Todo"
            if "Hecho" in props:
                hecho = props["Hecho"].get("checkbox", False)
                estado = "Completado" if hecho else "Todo"
            
            task = {
                "id": page.get("id"),
                "name": name,
                "status": estado,
                "url": page.get("url", "")
            }
            
            return task
        except Exception as e:
            print(f"⚠️ Error parseando tarea: {e}")
            return None
    
    # ============ COMANDOS DE TAREAS ============
    
    def get_tasks_formatted(self) -> str:
        """Obtiene tareas pendientes formateadas"""
        tasks = self.get_tasks(status="Todo", limit=10)
        if not tasks:
            return "🎉 ¡No tienes tareas pendientes!"
        
        lines = ["📋 Tareas pendientes:"]
        for i, task in enumerate(tasks, 1):
            lines.append(f"  {i}. {task['name']}")
        return "\n".join(lines)
    
    def search_task(self, name: str) -> str:
        """Busca una tarea por nombre"""
        if not name:
            return "¿Qué tarea quieres buscar?"
        
        tasks = self.get_tasks(limit=50)
        matching = [t for t in tasks if name.lower() in t['name'].lower()]
        
        if not matching:
            return f"No encontré tareas con '{name}'"
        
        if len(matching) == 1:
            task = matching[0]
            return f"📋 Encontré: '{task['name']}' - Estado: {task['status']}"
        else:
            lines = [f"Encontré {len(matching)} tareas:"]
            for i, task in enumerate(matching[:5], 1):
                lines.append(f"  {i}. {task['name']}")
            return "\n".join(lines)
    
    def create_task(self, name: str) -> str:
        """Crea una nueva tarea"""
        if not name:
            return "¿Qué tarea quieres crear?"
        
        try:
            url = f"{self.base_url}/pages"
            payload = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Nombre": {"title": [{"text": {"content": name}}]},
                    "Hecho": {"checkbox": False}
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return f"✅ Tarea '{name}' creada"
        except Exception as e:
            return f"❌ Error creando tarea: {e}"
    
    def complete_task(self, name: str) -> str:
        """Completa una tarea"""
        if not name:
            return "¿Qué tarea quieres completar?"
        
        tasks = self.get_tasks(limit=50)
        matching = [t for t in tasks if name.lower() in t['name'].lower()]
        
        if not matching:
            return f"No encontré tarea '{name}'"
        
        if len(matching) == 1:
            try:
                task_id = matching[0]['id']
                url = f"{self.base_url}/pages/{task_id}"
                payload = {
                    "properties": {
                        "Hecho": {"checkbox": True}
                    }
                }
                requests.patch(url, headers=self.headers, json=payload)
                return f"✅ Tarea '{matching[0]['name']}' completada"
            except Exception as e:
                return f"❌ Error: {e}"
        else:
            lines = [f"Encontré varias tareas:"]
            for i, task in enumerate(matching[:5], 1):
                lines.append(f"  {i}. {task['name']}")
            return "\n".join(lines)
    
    def delete_task(self, name: str) -> str:
        """Elimina una tarea"""
        if not name:
            return "¿Qué tarea quieres eliminar?"
        
        tasks = self.get_tasks(limit=50)
        matching = [t for t in tasks if name.lower() in t['name'].lower()]
        
        if not matching:
            return f"No encontré tarea '{name}'"
        
        if len(matching) == 1:
            try:
                task_id = matching[0]['id']
                url = f"{self.base_url}/pages/{task_id}"
                payload = {"archived": True}
                requests.patch(url, headers=self.headers, json=payload)
                return f"🗑️ Tarea '{matching[0]['name']}' eliminada"
            except Exception as e:
                return f"❌ Error: {e}"
        else:
            lines = [f"Encontré varias tareas:"]
            for i, task in enumerate(matching[:5], 1):
                lines.append(f"  {i}. {task['name']}")
            return "\n".join(lines)
    
    def get_tasks_today(self) -> str:
        """Tareas para hoy (por ahora muestra todas)"""
        return self.get_tasks_formatted()
    
    def get_completed_tasks(self) -> str:
        """Obtiene tareas completadas"""
        tasks = self.get_tasks(status="Completado", limit=10)
        if not tasks:
            return "No hay tareas completadas"
        lines = ["📋 Tareas completadas:"]
        for i, task in enumerate(tasks, 1):
            lines.append(f"  {i}. {task['name']} ✅")
        return "\n".join(lines)