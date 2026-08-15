# modules/telephone.py
import os
from twilio.rest import Client

class PhoneNotifier:
    def __init__(self):
        # Obtener credenciales de las variables de entorno
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.personal_number = os.getenv("PERSONAL_PHONE_NUMBER")
        
        # Inicializar el cliente de Twilio solo si las credenciales existen
        if all([self.account_sid, self.auth_token, self.twilio_number, self.personal_number]):
            self.client = Client(self.account_sid, self.auth_token)
            print("📞 Notificador telefónico de Twilio inicializado.")
        else:
            self.client = None
            print("⚠️ No se pudo inicializar Twilio. Revisa las variables de entorno.")

    def call_and_say(self, message: str):
        """Realiza una llamada y reproduce un mensaje de voz."""
        if not self.client:
            print("❌ Twilio no está configurado.")
            return False

        # En un caso real, aquí necesitarías una URL pública donde Twilio pueda obtener las instrucciones de voz.
        # La URL apuntaría a un endpoint de tu backend que genera el TwiML con el mensaje.
        # Ejemplo: ngrok te permite crear una URL temporal para desarrollo. [citation:6]
        webhook_url = "https://tu-url-publica.ngrok.io/voice/instructions" 

        print(f"📞 Intentando llamar a {self.personal_number} desde {self.twilio_number}...")

        try:
            call = self.client.calls.create(
                url=webhook_url, # Twilio consultará esta URL para saber qué decir
                to=self.personal_number,
                from_=self.twilio_number,
                status_callback=self.webhook_url + "/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            print(f"✅ Llamada iniciada. SID de la llamada: {call.sid}")
            return True
        except Exception as e:
            print(f"❌ Error al hacer la llamada: {e}")
            return False