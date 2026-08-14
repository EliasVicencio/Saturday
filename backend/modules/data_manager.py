# modules/data_manager.py - Versión MVP
import os
import json
from datetime import datetime
from typing import Dict, List

class DataManager:
    """Gestor de datos locales para Saturday - MVP"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.notes_file = os.path.join(data_dir, "notes.json")
        self.reminders_file = os.path.join(data_dir, "reminders.json")
        self.stats_file = os.path.join(data_dir, "stats.json")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        for file in [self.notes_file, self.reminders_file, self.stats_file]:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
    
    def create_note(self, text: str) -> str:
        if not text:
            return "¿Qué nota quieres guardar?"
        
        notes = self._get_notes()
        notes.append({
            "id": len(notes) + 1,
            "text": text,
            "created": datetime.now().isoformat()
        })
        self._save_notes(notes)
        return f"✅ Nota guardada"
    
    def get_notes(self) -> str:
        notes = self._get_notes()
        if not notes:
            return "No tienes notas guardadas"
        
        lines = ["📝 NOTAS:"]
        for i, note in enumerate(notes[-5:][::-1], 1):
            lines.append(f"  {i}. {note['text'][:60]}...")
        return "\n".join(lines)
    
    def search_notes(self, query: str) -> str:
        if not query:
            return "¿Qué quieres buscar?"
        
        notes = self._get_notes()
        results = [n for n in notes if query.lower() in n['text'].lower()]
        if not results:
            return f"No encontré notas con '{query}'"
        
        lines = [f"🔍 Resultados para '{query}':"]
        for i, note in enumerate(results[:5], 1):
            lines.append(f"  {i}. {note['text'][:60]}")
        return "\n".join(lines)
    
    def create_reminder(self, text: str) -> str:
        if not text:
            return "¿Qué recordatorio quieres crear?"
        
        # Extraer hora simple
        import re
        time_match = re.search(r'a las\s*(\d{1,2}):?(\d{2})?', text)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) or "00"
            time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"
            text = text.replace(time_match.group(0), "").strip()
        else:
            time_str = "09:00"
        
        reminders = self._get_reminders()
        reminders.append({
            "id": len(reminders) + 1,
            "text": text,
            "time": time_str,
            "created": datetime.now().isoformat()
        })
        self._save_reminders(reminders)
        return f"✅ Recordatorio: '{text}' a las {time_str}"
    
    def get_reminders(self) -> str:
        reminders = self._get_reminders()
        if not reminders:
            return "No tienes recordatorios"
        
        lines = ["⏰ RECORDATORIOS:"]
        for i, r in enumerate(reminders[-5:][::-1], 1):
            lines.append(f"  {i}. {r['text']} - {r['time']}")
        return "\n".join(lines)
    
    def get_reminders_today(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        reminders = self._get_reminders()
        today_reminders = [r for r in reminders if r['created'].startswith(today)]
        if not today_reminders:
            return "No tienes recordatorios para hoy"
        
        lines = ["⏰ RECORDATORIOS DE HOY:"]
        for i, r in enumerate(today_reminders, 1):
            lines.append(f"  {i}. {r['text']} - {r['time']}")
        return "\n".join(lines)
    
    def get_stats(self) -> str:
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        except:
            stats = {}
        
        if not stats:
            return "No hay estadísticas"
        
        lines = ["📊 ESTADÍSTICAS:"]
        lines.append(f"  📝 Comandos: {stats.get('total_commands', 0)}")
        lines.append(f"  📌 Notas: {stats.get('notes_count', 0)}")
        lines.append(f"  ⏰ Recordatorios: {stats.get('reminders_count', 0)}")
        return "\n".join(lines)
    
    def _get_notes(self) -> List[Dict]:
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_notes(self, notes: List[Dict]):
        with open(self.notes_file, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    
    def _get_reminders(self) -> List[Dict]:
        try:
            with open(self.reminders_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _save_reminders(self, reminders: List[Dict]):
        with open(self.reminders_file, 'w', encoding='utf-8') as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)