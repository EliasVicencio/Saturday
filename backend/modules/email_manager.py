# modules/email_manager.py
import os
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class EmailManager:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, credentials_path: str = "credentials/credentials.json"):
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        creds = None
        token_path = "credentials/token_email.json"
        
        if not os.path.exists("credentials"):
            os.makedirs("credentials")
        
        if os.path.exists(token_path):
            with open(token_path, 'r') as token:
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
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail autenticado")
    
    def get_emails_formatted(self) -> str:
        return "Correos (implementacion en progreso)"
    
    def get_unread_emails_formatted(self) -> str:
        return "Correos no leidos (implementacion en progreso)"
    
    def send_email_from_text(self, text: str) -> str:
        if not text:
            return "Que correo quieres enviar?"
        return "Correo enviado (implementacion en progreso)"