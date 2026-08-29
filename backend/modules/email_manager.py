# modules/email_manager.py - Gestion de correos via Gmail SMTP/IMAP
import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from typing import Dict, Any, List
import re


class EmailManager:
    """Gestiona correos electronicos via Gmail SMTP + IMAP."""
    
    def __init__(self):
        self.email = os.getenv("SATURDAY_EMAIL", "")
        self.password = os.getenv("SATURDAY_EMAIL_PASSWORD", "")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        
        if self.email and self.password:
            print(f"  Email: configurado ({self.email})")
        else:
            print("  Email: sin configurar")
    
    def _is_configured(self) -> bool:
        return bool(self.email and self.password)
    
    def _get_imap(self):
        """Conexion IMAP segura."""
        mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
        mail.login(self.email, self.password)
        return mail
    
    def get_emails_formatted(self) -> str:
        """Obtiene los correos recientes formateados."""
        if not self._is_configured():
            return "El correo no esta configurado."
        
        emails = self.get_recent_emails(limit=5)
        if not emails:
            return "No hay correos recientes."
        
        result = "Tus correos recientes:\n\n"
        for i, e in enumerate(emails, 1):
            result += f"{i}. De: {e['from']}\n"
            result += f"   Asunto: {e['subject']}\n"
            result += f"   Fecha: {e['date']}\n"
            result += f"   {e['preview']}\n\n"
        
        return result
    
    def get_unread_emails_formatted(self) -> str:
        """Obtiene los correos no leidos formateados."""
        if not self._is_configured():
            return "El correo no esta configurado."
        
        emails = self.get_unread_emails(limit=5)
        if not emails:
            return "No tienes correos no leidos."
        
        result = "Tus correos no leidos:\n\n"
        for i, e in enumerate(emails, 1):
            result += f"{i}. De: {e['from']}\n"
            result += f"   Asunto: {e['subject']}\n"
            result += f"   Fecha: {e['date']}\n"
            result += f"   {e['preview']}\n\n"
        
        return result
    
    def _fetch_emails(self, criteria: str = "ALL", limit: int = 5) -> List[Dict[str, str]]:
        """Metodo privado para buscar y fetchear correos."""
        mail = None
        try:
            mail = self._get_imap()
            mail.select("INBOX")
            
            _, msg_nums = mail.search(None, criteria)
            msg_list = msg_nums[0].split()
            
            recent = msg_list[-limit:] if len(msg_list) >= limit else msg_list
            recent.reverse()
            
            emails = []
            for num in recent:
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                emails.append({
                    "from": self._decode_header(msg["From"]),
                    "subject": self._decode_header(msg["Subject"]),
                    "date": msg["Date"],
                    "body": self._get_body(msg),
                })
            
            return emails
        
        except Exception as e:
            print(f"Error leyendo correos: {e}")
            return []
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass
    
    def get_recent_emails(self, limit: int = 5) -> List[Dict[str, str]]:
        """Obtiene los correos mas recientes."""
        emails = self._fetch_emails("ALL", limit)
        for e in emails:
            e["preview"] = e["body"][:150] + "..." if len(e["body"]) > 150 else e["body"]
        return emails
    
    def get_unread_emails(self, limit: int = 5) -> List[Dict[str, str]]:
        """Obtiene los correos no leidos."""
        emails = self._fetch_emails("UNSEEN", limit)
        for e in emails:
            e["preview"] = e["body"][:150] + "..." if len(e["body"]) > 150 else e["body"]
        return emails
    
    def _decode_header(self, header):
        """Decodifica headers de correo."""
        if not header:
            return ""
        decoded = decode_header(header)
        result = []
        for part, enc in decoded:
            if isinstance(part, bytes):
                result.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                result.append(part)
        return " ".join(result)
    
    def _get_body(self, msg):
        """Extrae el cuerpo del correo."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""
    
    def send_email_from_text(self, text: str) -> str:
        if not text:
            return "Que correo quieres enviar? Dame el destinatario y el mensaje."
        
        if not self._is_configured():
            return "El correo no esta configurado."
        
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
            return {"success": False, "error": "Error de autenticacion."}
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
