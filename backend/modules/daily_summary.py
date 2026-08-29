# modules/daily_summary.py
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from modules.http_utils import get_with_retry

class DailySummary:
    """Genera y envia resumenes diarios desde Saturday"""
    
    def __init__(self, core):
        self.core = core
        self.today = date.today()
        self.date_str = self.today.strftime("%d/%m/%Y")
        self.weekday = self._get_weekday()
    
    def _get_weekday(self) -> str:
        """Obtiene el nombre del dia de la semana"""
        dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        return dias[self.today.weekday()]
    
    def generate(self) -> str:
        """Genera el resumen diario completo"""
        summary = []
        
        # ===== HEADER =====
        summary.append(f"*RESUMEN DEL DIA*")
        summary.append(f" {self.weekday}, {self.date_str}")
        summary.append("")
        
        # ===== HORA =====
        ahora = datetime.now().strftime("%H:%M")
        summary.append(f"*Hora:* {ahora}")
        summary.append("")
        
        # ===== CLIMA =====
        clima = self._get_weather()
        if clima:
            summary.append(f"*Clima:* {clima}")
            summary.append("")
        
        # ===== TAREAS PENDIENTES =====
        tareas = self._get_tasks()
        if tareas:
            summary.append(f"*Tareas pendientes:*")
            for t in tareas:
                summary.append(f"  - {t}")
            summary.append("")
        else:
            summary.append("*Tareas pendientes:* !Ninguna!")
            summary.append("")
        
        # ===== EVENTOS DE HOY =====
        eventos = self._get_events()
        if eventos:
            summary.append(f"*Eventos de hoy:*")
            for e in eventos:
                summary.append(f"  - {e}")
            summary.append("")
        else:
            summary.append("*Eventos de hoy:* No hay eventos programados")
            summary.append("")
        
        # ===== RECORDATORIOS =====
        recordatorios = self._get_reminders()
        if recordatorios:
            summary.append(f"- *Recordatorios:*")
            for r in recordatorios:
                summary.append(f"  - {r}")
            summary.append("")
        else:
            summary.append("- *Recordatorios:* No tienes recordatorios")
            summary.append("")
        
        # ===== CORREOS REVISADOS (autonomo) =====
        correos = self._get_autonomous_emails()
        if correos:
            summary.append(f"*Correos revisados:*")
            summary.append(f"  {correos}")
            summary.append("")
        
        # ===== NOTICIAS DEL DIA (autonomo) =====
        noticias = self._get_autonomous_news()
        if noticias:
            summary.append(f"- *Noticias de hoy:*")
            summary.append(f"  {noticias}")
            summary.append("")
        
        # ===== FOOTER =====
        summary.append("")
        summary.append("*Para mas informacion:*")
        summary.append("  - 'tareas' - Ver todas las tareas")
        summary.append("  - 'eventos' - Ver todos los eventos")
        summary.append("  - 'recordatorios' - Ver todos los recordatorios")
        summary.append("  - 'clima' - Ver el clima completo")
        summary.append("")
        summary.append("*Saturday - Tu asistente personal*")
        
        return "\n".join(summary)
    
    def _get_weather(self) -> Optional[str]:
        """Obtiene el clima del dia"""
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            if not api_key:
                return None
            city = os.getenv("SATURDAY_CITY", "Santiago")
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = get_with_retry(url, timeout=10)
            if response and response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                return f"{desc}, {temp}oC"
            return None
        except (KeyError, TypeError, Exception):
            return None
    
    def _get_tasks(self) -> List[str]:
        """Obtiene tareas pendientes de Notion"""
        if not self.core.notion:
            return []
        try:
            tasks = self.core.notion.get_tasks(status="Todo", limit=5)
            return [f"{t['name']}" for t in tasks]
        except Exception:
            return []
    
    def _get_events(self) -> List[str]:
        """Obtiene eventos del calendario para hoy"""
        if not self.core.calendar:
            return []
        try:
            events = self.core.calendar.get_events_today()
            formatted = []
            for e in events:
                start = e.get('start', {}).get('dateTime', 'Todo el dia')
                if start and 'T' in start:
                    start = start.split('T')[1][:5]  # HH:MM
                formatted.append(f"{e.get('summary', 'Sin titulo')} - {start}")
            return formatted
        except Exception:
            return []
    
    def _get_reminders(self) -> List[str]:
        """Obtiene recordatorios del dia"""
        if not self.core.data:
            return []
        try:
            reminders = self.core.data.get_reminders_today()
            return [f"{r['text']} - {r['time']}" for r in reminders]
        except Exception:
            return []
    
    def _get_autonomous_emails(self) -> Optional[str]:
        """Obtiene correos revisados automaticamente de la boveda"""
        if not self.core.vault:
            return None
        try:
            results = self.core.vault.search("Correos no leidos")
            if results:
                latest = results[0]
                return latest.get('snippet', 'Correos revisados hoy')
            return None
        except Exception:
            return None
    
    def _get_autonomous_news(self) -> Optional[str]:
        """Obtiene noticias recolectadas automaticamente de la boveda"""
        if not self.core.vault:
            return None
        try:
            results = self.core.vault.search("Noticias")
            if results:
                news_items = []
                for r in results[:3]:
                    snippet = r.get('snippet', '')
                    if snippet:
                        news_items.append(snippet[:100])
                return '\n'.join(news_items) if news_items else None
            return None
        except Exception:
            return None
    
    def send(self, via: str = "whatsapp") -> Dict[str, Any]:
        """Envia el resumen por el canal especificado y lo guarda en la boveda"""
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
            try:
                self.core.telegram.send_message(summary)
                result = {'success': True, 'message': 'Resumen enviado por Telegram'}
            except Exception as e:
                result = {'success': False, 'error': f'Error enviando por Telegram: {str(e)}'}

        else:
            return {'success': False, 'error': f'Canal no soportado: {via}'}

        # Si el envio fue exitoso, dejamos rastro en la boveda ("si no esta en la
        # boveda, no paso"). Nunca dejamos que un fallo aca tumbe el envio ya hecho.
        if result.get('success') and self.core.vault:
            try:
                # 1) copia cruda del texto enviado, en outputs/
                output_path = self.core.vault.save_output(
                    summary, kind=f"resumen-diario-{via}"
                )
                # 2) nota enlazada en wiki/, agrupada bajo el hub "Resumenes Diarios"
                #    asi el resumen aparece como nodo conectado en el grafo de la boveda
                item_title = f"Resumen {self.date_str}"
                wiki_path = self.core.vault.link_into_hub(
                    hub_title="Resumenes Diarios",
                    item_title=item_title,
                    item_summary=summary,
                    source_path=output_path,
                    tags=["resumen-diario", via],
                )
                result['vault_path'] = output_path
                result['vault_wiki_path'] = wiki_path
            except Exception as e:
                print(f" No se pudo guardar el resumen en la boveda: {e}")

        return result
