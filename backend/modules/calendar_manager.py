# modules/calendar_manager.py
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class CalendarManager:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_path: str = "credentials/credentials.json"):
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        creds = None
        token_path = "credentials/token_calendar.pickle"
        
        if not os.path.exists("credentials"):
            os.makedirs("credentials")
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print("❌ No se encuentra credentials.json")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar autenticado")
    
    def get_events(self, max_results: int = 10) -> List[Dict]:
        if not self.service:
            return []
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            print(f"⚠️ Error obteniendo eventos: {e}")
            return []
    
    def get_events_formatted(self) -> str:
        events = self.get_events()
        if not events:
            return "No tienes eventos próximos"
        lines = ["📅 EVENTOS PRÓXIMOS:"]
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d/%m %H:%M')
                except:
                    date_str = start
            else:
                date_str = 'Sin fecha'
            lines.append(f"  • {event.get('summary', 'Sin título')} - {date_str}")
        return "\n".join(lines)
    
    def get_events_today_formatted(self) -> str:
        events = self.get_events()
        today = datetime.now().date()
        today_events = []
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    if dt.date() == today:
                        today_events.append(event)
                except:
                    pass
        
        if not today_events:
            return "No tienes eventos para hoy"
        lines = ["📅 EVENTOS DE HOY:"]
        for event in today_events:
            start = event.get('start', {}).get('dateTime', '')
            time_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%H:%M') if start else 'Todo el día'
            lines.append(f"  • {event.get('summary', 'Sin título')} - {time_str}")
        return "\n".join(lines)
    
    def get_events_today_list(self) -> list:
        """Igual que get_events_today_formatted pero devuelve datos estructurados (para la API)."""
        events = self.get_events()
        today = datetime.now().date()
        result = []
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            if not start:
                continue
            try:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                if dt.date() != today:
                    continue
                result.append({
                    'title': event.get('summary', 'Sin título'),
                    'time': dt.strftime('%H:%M') if 'T' in start else 'Todo el día',
                })
            except Exception:
                continue
        return result

    def create_event_from_text(self, text: str) -> str:
        if not text:
            return "¿Qué evento quieres crear?"
        return "✅ Evento creado (implementación en progreso)"