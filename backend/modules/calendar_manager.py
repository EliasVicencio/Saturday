# modules/calendar_manager.py
import os
import json
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
        token_path = "credentials/token_calendar.json"
        
        if not os.path.exists("credentials"):
            os.makedirs("credentials")
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print("No se encuentra credentials.json")
                    return
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar autenticado")
    
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
            print(f"Error obteniendo eventos: {e}")
            return []
    
    def get_events_formatted(self) -> str:
        events = self.get_events()
        if not events:
            return "No tienes eventos proximos"
        lines = ["EVENTOS PROXIMOS:"]
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            if start:
                try:
                    dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d/%m %H:%M')
                except (ValueError, TypeError):
                    date_str = start
            else:
                date_str = 'Sin fecha'
            lines.append(f"  - {event.get('summary', 'Sin titulo')} - {date_str}")
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
                except (ValueError, TypeError):
                    pass
        
        if not today_events:
            return "No tienes eventos para hoy"
        lines = ["EVENTOS DE HOY:"]
        for event in today_events:
            start = event.get('start', {}).get('dateTime', '')
            time_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%H:%M') if start else 'Todo el dia'
            lines.append(f"  - {event.get('summary', 'Sin titulo')} - {time_str}")
        return "\n".join(lines)
    
    def get_events_today_list(self) -> list:
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
                    'title': event.get('summary', 'Sin titulo'),
                    'time': dt.strftime('%H:%M') if 'T' in start else 'Todo el dia',
                })
            except Exception:
                continue
        return result

    def create_event_from_text(self, text: str) -> str:
        if not text:
            return "Que evento quieres crear?"
        
        if not self.service:
            return "Google Calendar no esta configurado. Necesitas credentials.json."
        
        import re
        from datetime import datetime, timedelta
        
        text_lower = text.lower()
        
        # Extraer titulo
        title = text
        for word in ["crear evento", "agenda un evento", "agrega un evento", "evento"]:
            title = title.replace(word, "").strip()
        if not title:
            title = "Evento sin titulo"
        
        # Extraer fecha/hora basica
        now = datetime.now()
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        if "ma" in text_lower:
            start_time = start_time + timedelta(days=1)
            end_time = end_time + timedelta(days=1)
        
        hour_match = re.search(r"a las (\d{1,2})(?::(\d{2}))?", text_lower)
        if hour_match:
            hour = int(hour_match.group(1))
            minute = int(hour_match.group(2) or 0)
            start_time = start_time.replace(hour=hour, minute=minute)
            end_time = start_time + timedelta(hours=1)
        
        try:
            event = {
                "summary": title,
                "start": {"dateTime": start_time.isoformat(), "timeZone": "America/Santiago"},
                "end": {"dateTime": end_time.isoformat(), "timeZone": "America/Santiago"},
            }
            created = self.service.events().insert(calendarId="primary", body=event).execute()
            return f"Evento creado: {title} el {start_time.strftime('%d/%m %H:%M')}"
        except Exception as e:
            return f"Error creando evento: {str(e)}"