# modules/email_manager.py - Gestion de correos via Gmail SMTP directo
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import re


class EmailManager:
    """Gestiona correos electronicos via Gmail SMTP."""
    
    def __init__(self):
        self.email = os.getenv("SATURDAY_EMAIL", "")
        self.password = os.getenv("SATURDAY_EMAIL_PASSWORD", "")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        if self.email and self.password:
            print(f"  Email: configurado ({self.email})")
        else:
            print("  Email: sin configurar (SATURDAY_EMAIL / SATURDAY_EMAIL_PASSWORD)")
    
    def _is_configured(self) -> bool:
        return bool(self.email and self.password)
    
    def get_emails_formatted(self) -> str:
        if not self._is_configured():
            return "El correo no esta configurado. Necesitas configurar SATURDAY_EMAIL y SATURDAY_EMAIL_PASSWORD en .env"
        return (
            "Puedo enviar correos desde tu Gmail.\n"
            "Ejemplo: 'envia un correo a alguien@example.com sobre asunto'\n"
            "Nota: Por ahora solo puedo enviar, no leer correos."
        )
    
    def get_unread_emails_formatted(self) -> str:
        if not self._is_configured():
            return "El correo no esta configurado."
        return "Por ahora solo puedo enviar correos. La lectura de correos requiere Gmail API."
    
    def send_email_from_text(self, text: str) -> str:
        if not text:
            return "Que correo quieres enviar? Dame el destinatario y el mensaje."
        
        if not self._is_configured():
            return "El correo no esta configurado. Necesitas configurar SATURDAY_EMAIL y SATURDAY_EMAIL_PASSWORD en .env"
        
        parsed = self._parse_email_text(text)
        if not parsed.get("to"):
            return "Necesito saber a quien enviar el correo. Ejemplo: 'envia un correo a Juan sobre la reunion'"
        
        result = self.send_email(
            to=parsed["to"],
            subject=parsed.get("subject", "Correo desde Saturday"),
            body=parsed.get("body", text),
        )
        
        if result["success"]:
            return f"Correo enviado a {parsed['to']}!"
        else:
            return f"Error enviando correo: {result.get('error', 'Error desconocido')}"
    
    def send_email(self, to: str, subject: str, body: str, cc: str = "") -> Dict[str, Any]:
        """Envia un correo via Gmail SMTP."""
        if not self._is_configured():
            return {"success": False, "error": "Correo no configurado"}
        
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return {"success": True, "to": to}
        
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "error": "Error de autenticacion. Verifica la contrasena de aplicacion."}
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"Error SMTP: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_email_text(self, text: str) -> Dict[str, str]:
        result = {"to": "", "subject": "", "body": text}
        
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            result["to"] = email_match.group(0)
        
        if not result["to"]:
            to_match = re.search(r'a\s+(\w+)', text.lower())
            if to_match:
                name = to_match.group(1).strip()
                skip_words = ["ti", "vos", "el", "ella", "nosotros", "ustedes", "alguien", "nadie", "todos"]
                if name not in skip_words:
                    result["to"] = name
        
        subject_match = re.search(r'sobre\s+(.+?)(?:\.|$)', text.lower())
        if subject_match:
            result["subject"] = subject_match.group(1).strip()
        
        return result
