# modules/scheduler.py
import schedule
import time
import threading
from datetime import datetime
from typing import Callable, Optional

class Scheduler:
    """Gestor de tareas programadas para Saturday"""
    
    def __init__(self, core):
        self.core = core
        self.jobs = []
        self.is_running = False
        self.thread = None
        
        print(" Scheduler inicializado")
    
    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(" Scheduler iniciado en segundo plano")
    
    def _run(self):
        """Ejecuta el bucle del scheduler"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Detiene el scheduler"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        print(" Scheduler detenido")
    
    def send_daily_summary(self):
        """Envía el resumen diario"""
        print(f" Enviando resumen diario programado... {datetime.now()}")
        if self.core.daily_summary:
            result = self.core.daily_summary.send(via="whatsapp")
            if result.get('success'):
                print(" Resumen diario enviado")
            else:
                print(f" Error enviando resumen: {result.get('error')}")
        else:
            print(" DailySummary no disponible")
    
    def schedule_daily_summary(self, hour: int = 8, minute: int = 0):
        """Programa el envío del resumen diario"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.send_daily_summary)
        self.jobs.append({
            'type': 'daily_summary',
            'hour': hour,
            'minute': minute
        })
        print(f" Resumen diario programado para las {hour:02d}:{minute:02d}")
    
    # ============ TAREAS AUTÓNOMAS ============
    
    def check_emails_autonomously(self):
        """Revisa correos y guarda resumen en la bóveda"""
        print(f" Revisando correos automáticamente... {datetime.now()}")
        if not self.core.email:
            print(" Email no disponible")
            return
        
        try:
            emails = self.core.email.get_unread_emails_formatted()
            if emails and "No hay correos" not in emails:
                # Guardar en la bóveda
                if self.core.vault:
                    self.core.vault.save_raw(
                        f"Correos no leídos ({datetime.now().strftime('%H:%M')}):\n{emails}",
                        source="autonomo"
                    )
                print(f" Correos revisados y guardados")
            else:
                print(" No hay correos nuevos")
        except Exception as e:
            print(f" Error revisando correos: {e}")
    
    def collect_news_autonomously(self):
        """Recolecta noticias del día y guarda en la bóveda"""
        print(f" Recolectando noticias automáticamente... {datetime.now()}")
        if not self.core.news or not self.core.news.is_available():
            print(" News no disponible")
            return
        
        try:
            articles = self.core.news.get_top_headlines(limit=5)
            if articles:
                # Formatear para guardar
                news_text = "Noticias del día:\n"
                for i, article in enumerate(articles, 1):
                    news_text += f"{i}. {article.get('title', 'Sin título')}\n"
                
                # Guardar en la bóveda
                if self.core.vault:
                    self.core.vault.save_raw(
                        f"Noticias ({datetime.now().strftime('%d/%m %H:%M')}):\n{news_text}",
                        source="autonomo"
                    )
                print(f" {len(articles)} noticias recolectadas")
            else:
                print(" No se encontraron noticias")
        except Exception as e:
            print(f" Error recolectando noticias: {e}")
    
    def organize_data_autonomously(self):
        """Organiza y resume datos del día"""
        print(f" Organizando datos del día... {datetime.now()}")
        try:
            # Obtener estadísticas
            if self.core.data:
                stats = self.core.data.get_stats()
                print(f" Estadísticas: {stats}")
        except Exception as e:
            print(f" Error organizando datos: {e}")
    
    def schedule_autonomous_tasks(self):
        """Programa todas las tareas autónomas"""
        # Revisar correos cada 4 horas
        schedule.every(4).hours.do(self.check_emails_autonomously)
        print(" Revisión de correos programada (cada 4h)")
        
        # Recolectar noticias a las 8:00 AM
        schedule.every().day.at("08:00").do(self.collect_news_autonomously)
        print(" Recolectar noticias programada (08:00)")
        
        # Organizar datos a las 20:00 (antes del resumen)
        schedule.every().day.at("20:00").do(self.organize_data_autonomously)
        print(" Organizar datos programada (20:00)")
    
    def schedule_reminder(self, text: str, hour: int, minute: int):
        """Programa un recordatorio"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
            self._send_reminder, text
        )
        print(f" Recordatorio programado: '{text}' a las {hour:02d}:{minute:02d}")
    
    def _send_reminder(self, text: str):
        """Envía un recordatorio programado"""
        print(f" Enviando recordatorio: {text}")
        if self.core.communication:
            self.core.communication.send_whatsapp_message(f" RECORDATORIO: {text}")
    
    def list_jobs(self) -> list:
        """Lista las tareas programadas"""
        jobs = []
        for job in schedule.jobs:
            jobs.append({
                'next_run': str(job.next_run),
                'interval': str(job.interval),
                'unit': str(job.unit)
            })
        return jobs