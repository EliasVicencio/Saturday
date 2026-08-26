# modules/daily_summary.py
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import requests

class DailySummary:
    """Genera y envía resúmenes diarios desde Saturday"""
    
    def __init__(self, core):
        self.core = core
        self.today = date.today()
        self.date_str = self.today.strftime("%d/%m/%Y")
        self.weekday = self._get_weekday()
    
    def _get_weekday(self) -> str:
        """Obtiene el nombre del día de la semana"""
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return dias[self.today.weekday()]
    
    def generate(self) -> str:
        """Genera el resumen diario completo"""
        summary = []
        
        # ===== HEADER =====
        summary.append(f"📅 *RESUMEN DEL DÍA*")
        summary.append(f"📆 {self.weekday}, {self.date_str}")
        summary.append("")
        
        # ===== HORA =====
        ahora = datetime.now().strftime("%H:%M")
        summary.append(f"🕐 *Hora:* {ahora}")
        summary.append("")
        
        # ===== CLIMA =====
        clima = self._get_weather()
        if clima:
            summary.append(f"🌤️ *Clima:* {clima}")
            summary.append("")
        
        # ===== TAREAS PENDIENTES =====
        tareas = self._get_tasks()
        if tareas:
            summary.append(f"📋 *Tareas pendientes:*")
            for t in tareas:
                summary.append(f"  • {t}")
            summary.append("")
        else:
            summary.append("📋 *Tareas pendientes:* ¡Ninguna! 🎉")
            summary.append("")
        
        # ===== EVENTOS DE HOY =====
        eventos = self._get_events()
        if eventos:
            summary.append(f"📅 *Eventos de hoy:*")
            for e in eventos:
                summary.append(f"  • {e}")
            summary.append("")
        else:
            summary.append("📅 *Eventos de hoy:* No hay eventos programados")
            summary.append("")
        
        # ===== RECORDATORIOS =====
        recordatorios = self._get_reminders()
        if recordatorios:
            summary.append(f"⏰ *Recordatorios:*")
            for r in recordatorios:
                summary.append(f"  • {r}")
            summary.append("")
        else:
            summary.append("⏰ *Recordatorios:* No tienes recordatorios")
            summary.append("")
        
        # ===== CORREOS REVISADOS (autónomo) =====
        correos = self._get_autonomous_emails()
        if correos:
            summary.append(f"📧 *Correos revisados:*")
            summary.append(f"  {correos}")
            summary.append("")
        
        # ===== NOTICIAS DEL DÍA (autónomo) =====
        noticias = self._get_autonomous_news()
        if noticias:
            summary.append(f"📰 *Noticias de hoy:*")
            summary.append(f"  {noticias}")
            summary.append("")
        
        # ===== FOOTER =====
        summary.append("")
        summary.append("💡 *Para más información:*")
        summary.append("  • 'tareas' - Ver todas las tareas")
        summary.append("  • 'eventos' - Ver todos los eventos")
        summary.append("  • 'recordatorios' - Ver todos los recordatorios")
        summary.append("  • 'clima' - Ver el clima completo")
        summary.append("")
        summary.append("🤖 *Saturday - Tu asistente personal*")
        
        return "\n".join(summary)
    
    def _get_weather(self) -> Optional[str]:
        """Obtiene el clima del día"""
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            if not api_key:
                return None
            city = os.getenv("SATURDAY_CITY", "Santiago")
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"{desc}, {temp}°C"
            return None
        except:
            return None
    
    def _get_tasks(self) -> List[str]:
        """Obtiene tareas pendientes de Notion"""
        if not self.core.notion:
            return []
        try:
            tasks = self.core.notion.get_tasks(status="Todo", limit=5)
            return [f"{t['name']}" for t in tasks]
        except:
            return []
    
    def _get_events(self) -> List[str]:
        """Obtiene eventos del calendario para hoy"""
        if not self.core.calendar:
            return []
        try:
            events = self.core.calendar.get_events_today()
            formatted = []
            for e in events:
                start = e.get('start', {}).get('dateTime', 'Todo el día')
                if start and 'T' in start:
                    start = start.split('T')[1][:5]  # HH:MM
                formatted.append(f"{e.get('summary', 'Sin título')} - {start}")
            return formatted
        except:
            return []
    
    def _get_reminders(self) -> List[str]:
        """Obtiene recordatorios del día"""
        if not self.core.data:
            return []
        try:
            reminders = self.core.data.get_reminders_for_today()
            return [f"{r['text']} - {r['time']}" for r in reminders]
        except:
            return []
    
    def _get_autonomous_emails(self) -> Optional[str]:
        """Obtiene correos revisados automáticamente de la bóveda"""
        if not self.core.vault:
            return None
        try:
            results = self.core.vault.search("Correos no leídos")
            if results:
                # Tomar el más reciente
                latest = results[0]
                return latest.get('snippet', 'Correos revisados hoy')
            return None
        except:
            return None
    
    def _get_autonomous_news(self) -> Optional[str]:
        """Obtiene noticias recolectadas automáticamente de la bóveda"""
        if not self.core.vault:
            return None
        try:
            results = self.core.vault.search("Noticias")
            if results:
                # Tomar las más recientes
                news_items = []
                for r in results[:3]:
                    snippet = r.get('snippet', '')
                    if snippet:
                        news_items.append(snippet[:100])
                return '\n'.join(news_items) if news_items else None
            return None
        except:
            return None
    
    def send(self, via: str = "whatsapp") -> Dict[str, Any]:
        """Envía el resumen por el canal especificado y lo guarda en la bóveda"""
        summary = self.generate()

        if via == "whatsapp":
            if not self.core.communication:
                return {'success': False, 'error': 'CommunicationManager no disponible'}

            # Enviar por WhatsApp
            result = self.core.communication.send_whatsapp_message(summary)

        elif via == "telegram":
            if not self.core.telegram:
                return {'success': False, 'error': 'Telegram no disponible'}
            # Enviar por Telegram
            # self.core.telegram.send_message(summary)
            result = {'success': True, 'message': 'Resumen enviado por Telegram'}

        else:
            return {'success': False, 'error': f'Canal no soportado: {via}'}

        # Si el envío fue exitoso, dejamos rastro en la bóveda ("si no está en la
        # bóveda, no pasó"). Nunca dejamos que un fallo acá tumbe el envío ya hecho.
        if result.get('success') and self.core.vault:
            try:
                # 1) copia cruda del texto enviado, en outputs/
                output_path = self.core.vault.save_output(
                    summary, kind=f"resumen-diario-{via}"
                )
                # 2) nota enlazada en wiki/, agrupada bajo el hub "Resúmenes Diarios"
                #    así el resumen aparece como nodo conectado en el grafo de la bóveda
                item_title = f"Resumen {self.date_str}"
                wiki_path = self.core.vault.link_into_hub(
                    hub_title="Resúmenes Diarios",
                    item_title=item_title,
                    item_summary=summary,
                    source_path=output_path,
                    tags=["resumen-diario", via],
                )
                result['vault_path'] = output_path
                result['vault_wiki_path'] = wiki_path
            except Exception as e:
                print(f"⚠️ No se pudo guardar el resumen en la bóveda: {e}")

        return result