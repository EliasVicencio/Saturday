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
        
        print("⏰ Scheduler inicializado")
    
    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("⏰ Scheduler iniciado en segundo plano")
    
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
        print("⏰ Scheduler detenido")
    
    def send_daily_summary(self):
        """Envía el resumen diario"""
        print(f"📋 Enviando resumen diario programado... {datetime.now()}")
        if self.core.daily_summary:
            result = self.core.daily_summary.send(via="whatsapp")
            if result.get('success'):
                print("✅ Resumen diario enviado")
            else:
                print(f"❌ Error enviando resumen: {result.get('error')}")
        else:
            print("❌ DailySummary no disponible")
    
    def schedule_daily_summary(self, hour: int = 8, minute: int = 0):
        """Programa el envío del resumen diario"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.send_daily_summary)
        self.jobs.append({
            'type': 'daily_summary',
            'hour': hour,
            'minute': minute
        })
        print(f"📋 Resumen diario programado para las {hour:02d}:{minute:02d}")
    
    def schedule_reminder(self, text: str, hour: int, minute: int):
        """Programa un recordatorio"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
            self._send_reminder, text
        )
        print(f"⏰ Recordatorio programado: '{text}' a las {hour:02d}:{minute:02d}")
    
    def _send_reminder(self, text: str):
        """Envía un recordatorio programado"""
        print(f"⏰ Enviando recordatorio: {text}")
        if self.core.communication:
            self.core.communication.send_whatsapp_message(f"⏰ RECORDATORIO: {text}")
    
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