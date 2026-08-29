# modules/email_manager.py - Gestion de correos via Zapier webhooks
from typing import Dict, Any, Optional


class EmailManager:
    """Gestiona correos electronicos via Zapier ? Gmail."""
    
    def __init__(self, zapier=None):
        self.zapier = zapier
    
    def get_emails_formatted(self) -> str:
        if not self.zapier or not self.zapier.is_available("email"):
            return "Los correos no estan configurados. Configura un webhook de Zapier para Gmail."
        return (
            "Puedo ayudarte con correos via Zapier.\n"
            "Opciones: 'revisa mis correos', 'envia un correo a [nombre]'\n"
            "Nota: La lectura de correos requiere un Zap con trigger de Gmail."
        )
    
    def get_unread_emails_formatted(self) -> str:
        if not self.zapier or not self.zapier.is_available("email"):
            return "Los correos no estan configurados."
        return "Consultando correos no leidos via Zapier..."
    
    def send_email_from_text(self, text: str) -> str:
        if not text:
            return "Que correo quieres enviar? Dame el destinatario y el mensaje."
        
        if not self.zapier or not self.zapier.is_available("email"):
            return "Los correos no estan configurados. Configura un webhook de Zapier para Gmail."
        
        parsed = self._parse_email_text(text)
        if not parsed.get("to"):
            return "Necesito saber a quien enviar el correo. Ejemplo: 'envia un correo a Juan sobre la reunion'"
        
        result = self.zapier.send_email(
            to=parsed["to"],
            subject=parsed.get("subject", "Correo desde Saturday"),
            body=parsed.get("body", text),
        )
        
        if result["success"]:
            return f"Correo enviado a {parsed['to']}!"
        else:
            return f"Error enviando correo: {result.get('error', 'Error desconocido')}"
    
    def _parse_email_text(self, text: str) -> Dict[str, str]:
        """Interpreta texto del usuario para extraer destinatario, asunto y cuerpo."""
        result = {"to": "", "subject": "", "body": text}
        
        text_lower = text.lower()
        
        # Buscar patron "a [nombre]"
        import re
        to_match = re.search(r'a\s+(\w+(?:\s+\w+)?)', text_lower)
        if to_match:
            result["to"] = to_match.group(1).strip()
        
        # Buscar patron "sobre [asunto]"
        subject_match = re.search(r'sobre\s+(.+?)(?:\.|$)', text_lower)
        if subject_match:
            result["subject"] = subject_match.group(1).strip()
        
        return result
