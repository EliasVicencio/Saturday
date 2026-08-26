# modules/telegram_bot.py - Telegram Bot para Saturday (servicio independiente)
"""
Bot de Telegram que corre como servicio separado de Gunicorn.
Maneja mensajes de texto y voz, con botones inline para acciones comunes.
"""
import os
import sys
import logging
import asyncio
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

# Agregar directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Texto de ayuda por defecto
HELP_TEXT = """🤖 **Saturday - Asistente Personal**

📋 **TAREAS**
• `tareas` - Ver tareas pendientes
• `crear tarea [nombre]` - Crear tarea
• `completar tarea [nombre]` - Completar tarea

📝 **NOTAS**
• `nota [texto]` - Guardar nota
• `ver notas` - Ver notas

⏰ **RECORDATORIOS**
• `recordatorio [texto]` - Crear recordatorio
• `ver recordatorios` - Ver recordatorios

📅 **CALENDARIO**
• `eventos` - Ver eventos
• `eventos hoy` - Eventos de hoy

📧 **EMAILS**
• `correos` - Ver correos
• `no leídos` - Correos no leídos

📰 **NOTICIAS**
• `noticias` - Noticias principales
• `buscar noticias [tema]` - Buscar noticias

🕐 **UTILIDADES**
• `hora` - Hora actual
• `fecha` - Fecha actual
• `clima` - Clima
• `ayuda` - Esta ayuda

🎤 **VOZ**
• Envia un mensaje de voz y lo procesaré
"""

# Botones inline para acciones rápidas
MAIN_KEYBOARD = [
    [
        InlineKeyboardButton("📋 Tareas", callback_data="tareas"),
        InlineKeyboardButton("📰 Noticias", callback_data="noticias"),
    ],
    [
        InlineKeyboardButton("🕐 Hora", callback_data="hora"),
        InlineKeyboardButton("🌤️ Clima", callback_data="clima"),
    ],
    [
        InlineKeyboardButton("📅 Eventos Hoy", callback_data="eventos_hoy"),
        InlineKeyboardButton("📧 No Leídos", callback_data="no_leidos"),
    ],
    [
        InlineKeyboardButton("❓ Ayuda", callback_data="ayuda"),
    ],
]


class SaturdayTelegramBot:
    """Bot de Telegram para Saturday - Servicio Independiente"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.core = None
        self.application = None
        self._chat_ids = set()  # Soporte multi-chat
        
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN no configurado")
            return
        
        logger.info("🤖 Inicializando bot de Telegram...")
    
    def _init_core(self):
        """Inicializa SaturdayCore de forma lazy"""
        if self.core is not None:
            return True
        
        try:
            from modules.core import SaturdayCore
            self.core = SaturdayCore()
            logger.info("✅ SaturdayCore inicializado para Telegram")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando SaturdayCore: {e}")
            return False
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Bienvenida con botones"""
        self._chat_ids.add(update.effective_chat.id)
        
        welcome = (
            "¡Hola! Soy **Saturday**, tu asistente personal. 🟣\n\n"
            "Puedes escribirme o enviarme voz. Usa los botones o escribe comandos.\n\n"
            "Escribe /ayuda para ver todo lo que puedo hacer."
        )
        
        reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
        await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda"""
        reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
        await update.message.reply_text(HELP_TEXT, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja botones inline"""
        query = update.callback_query
        await query.answer()
        
        if not self._init_core():
            await query.edit_message_text("⚠️ Saturday no está listo aún. Intenta de nuevo en unos segundos.")
            return
        
        # Procesar como intención
        text = query.data
        result = self.core.process_intent(text)
        
        # Editar el mensaje con la respuesta
        response = result.get('response', 'No pude procesar eso.')
        
        # Mantener botones después de responder
        reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
        await query.edit_message_text(response, reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto"""
        self._chat_ids.add(update.effective_chat.id)
        
        if not self._init_core():
            await update.message.reply_text("⚠️ Saturday no está listo aún. Intenta de nuevo en unos segundos.")
            return
        
        user_message = update.message.text
        logger.info(f"📩 Mensaje de {update.effective_chat.id}: {user_message}")
        
        try:
            result = self.core.process_intent(user_message)
            response = result.get('response', 'No pude procesar eso.')
            
            # Agregar botones al final
            reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
            await update.message.reply_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de voz"""
        self._chat_ids.add(update.effective_chat.id)
        
        if not self._init_core():
            await update.message.reply_text("⚠️ Saturday no está listo aún.")
            return
        
        await update.message.reply_text("🎤 Procesando audio...")
        
        try:
            # Descargar el archivo de voz
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            # Guardar temporalmente
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
                await file.download_to_drive(tmp.name)
                tmp_path = tmp.name
            
            # Convertir a WAV usando ffmpeg
            wav_path = tmp_path.replace('.ogg', '.wav')
            subprocess.run(['ffmpeg', '-i', tmp_path, '-ar', '16000', '-ac', '1', wav_path, '-y'], 
                         capture_output=True, check=True)
            
            # Transcribir usando Google STT del core
            if self.core.voice:
                transcription = self.core.voice.transcribe_file(wav_path)
                if transcription:
                    await update.message.reply_text(f"📝 Escuché: _{transcription}_", parse_mode='Markdown')
                    
                    # Procesar la transcripción como texto
                    result = self.core.process_intent(transcription)
                    response = result.get('response', 'No pude procesar eso.')
                    reply_markup = InlineKeyboardMarkup(MAIN_KEYBOARD)
                    await update.message.reply_text(response, reply_markup=reply_markup)
                else:
                    await update.message.reply_text("❌ No pude entender el audio. Intenta de nuevo.")
            else:
                await update.message.reply_text("❌ STT no disponible en el backend.")
            
            # Limpiar archivos temporales
            os.unlink(tmp_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
                
        except Exception as e:
            logger.error(f"❌ Error procesando voz: {e}")
            await update.message.reply_text(f"❌ Error procesando audio: {str(e)}")
    
    def send_message(self, text: str, chat_id: int = None):
        """Envía un mensaje proactivamente (para notificaciones, resúmenes, etc.)"""
        if not self.application:
            return
        
        target_chat = chat_id or (next(iter(self._chat_ids)) if self._chat_ids else None)
        if not target_chat:
            logger.warning("⚠️ No hay chat_id para enviar mensaje")
            return
        
        try:
            # Ejecutar en el event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si ya hay un loop corriendo, crear una tarea
                asyncio.create_task(self._send_async(target_chat, text))
            else:
                loop.run_until_complete(self._send_async(target_chat, text))
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
    
    async def _send_async(self, chat_id: int, text: str):
        """Envío asíncrono interno"""
        try:
            await self.application.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"❌ Error en envío async: {e}")
    
    def run(self):
        """Inicia el bot con polling"""
        if not self.token:
            return
        
        if not self._init_core():
            logger.error("❌ No se pudo inicializar SaturdayCore")
            return
        
        self.application = Application.builder().token(self.token).build()
        
        # Handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("ayuda", self.cmd_help))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("🚀 Bot de Telegram iniciado con polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Punto de entrada para el servicio"""
    bot = SaturdayTelegramBot()
    bot.run()


if __name__ == '__main__':
    main()
