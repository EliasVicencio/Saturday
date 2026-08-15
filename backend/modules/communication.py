# modules/communication.py
import os
import requests
import urllib.parse
from typing import Dict, Any, Optional

class CommunicationManager:
    """Gestor de comunicaciones para Saturday (WhatsApp + Notificaciones)"""
    
    def __init__(self):
        # ===== WHATSAPP (CallMeBot) =====
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER")
        self.whatsapp_api_key = os.getenv("WHATSAPP_API_KEY")
        self.whatsapp_enabled = bool(self.whatsapp_number and self.whatsapp_api_key)
        
        print("📱 CommunicationManager inicializado")
        print(f"   WhatsApp: {'✅ Activado' if self.whatsapp_enabled else '❌ No configurado'}")
    
    # ================================================================
    # WHATSAPP (CallMeBot)
    # ================================================================
    
    def send_whatsapp_message(self, message: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Envía un mensaje por WhatsApp usando CallMeBot"""
        if not self.whatsapp_enabled:
            return {'success': False, 'error': 'WhatsApp no configurado'}
        
        target_phone = phone or self.whatsapp_number
        if not target_phone:
            return {'success': False, 'error': 'Número no especificado'}
        
        # Limpiar el mensaje de comandos
        for word in ["envía WhatsApp", "enviar WhatsApp", "envía wsp", "enviar wsp", "whatsapp"]:
            message = message.replace(word, "").strip()
        
        if not message:
            return {'success': False, 'error': 'Mensaje vacío'}
        
        try:
            encoded_message = urllib.parse.quote_plus(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={target_phone}&apikey={self.whatsapp_api_key}&text={encoded_message}"
            
            print(f"📤 Enviando WhatsApp a {target_phone}: {message}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ WhatsApp enviado")
                return {'success': True, 'message': 'WhatsApp enviado'}
            else:
                return {'success': False, 'error': f'Error {response.status_code}: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_whatsapp_voice(self, message: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Envía un mensaje de voz por WhatsApp"""
        if not self.whatsapp_enabled:
            return {'success': False, 'error': 'WhatsApp no configurado'}
        
        target_phone = phone or self.whatsapp_number
        if not target_phone:
            return {'success': False, 'error': 'Número no especificado'}
        
        # Limpiar el mensaje de comandos
        for word in ["envía voz WhatsApp", "enviar voz WhatsApp", "voz WhatsApp", "whatsapp voz"]:
            message = message.replace(word, "").strip()
        
        if not message:
            return {'success': False, 'error': 'Mensaje vacío'}
        
        try:
            encoded_message = urllib.parse.quote_plus(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={target_phone}&apikey={self.whatsapp_api_key}&text={encoded_message}&voice=es-ES-Standard-A"
            
            print(f"🎤 Enviando WhatsApp con voz a {target_phone}: {message}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ WhatsApp con voz enviado")
                return {'success': True, 'message': 'WhatsApp con voz enviado'}
            else:
                return {'success': False, 'error': f'Error {response.status_code}: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}