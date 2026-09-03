# modules/telegram_bot.py - Telegram Bot para Saturday (servicio independiente)
"""
Bot de Telegram integrado con el sistema completo de Saturday.
Usa process_via_router() como la web - mismo pipeline, mismas capacidades.
"""
import os
import sys
import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

HELP_TEXT = """周六 - Asistente Personal

Escribe cualquier cosa y te ayudo. Ejemplos:

"Tareas" - Ver tareas pendientes
"Crear tarea comprar leche" - Crear tarea
"Nota comprar regalo" - Guardar nota
"Resumen de correos" - Analizar tus correos
"¿Qué hora es?" - Hora actual
"¿Qué tiempo hace?" - Clima
"Noticias de tecnología" - Buscar noticias
"Recordatorio llamar a las 3" - Crear recordatorio

También puedes enviarme mensajes de voz."""


class SaturdayTelegramBot:
    """Bot de Telegram integrado con Saturday - Usa el mismo pipeline que la web"""
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.core = None
        self.application = None
        self._chat_sessions = {}  # chat_id -> session_id
        
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN no configurado")
            return
        
        logger.info("Inicializando bot de Telegram...")
    
    def _init_core(self):
        """Inicializa SaturdayCore de forma lazy"""
        if self.core is not None:
            return True
        
        try:
            from modules.core import SaturdayCore
            self.core = SaturdayCore()
            logger.info("SaturdayCore inicializado para Telegram")
            return True
        except Exception as e:
            logger.error(f"Error inicializando SaturdayCore: {e}")
            return False
    
    def _get_session_id(self, chat_id: int) -> str:
        """Obtiene o crea session_id para un chat"""
        if chat_id not in self._chat_sessions:
            self._chat_sessions[chat_id] = f"tg_{chat_id}"
        return self._chat_sessions[chat_id]
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Bienvenida limpia"""
        if not self._init_core():
            await update.message.reply_text("Saturday no esta listo. Intenta en unos segundos.")
            return
        
        welcome = (
            "Hola! Soy Saturday, tu asistente personal.\n\n"
            "Escribe cualquier cosa o envia un mensaje de voz.\n"
            "Usa /ayuda para ver comandos."
        )
        await update.message.reply_text(welcome)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda"""
        await update.message.reply_text(HELP_TEXT)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto - Mismo pipeline que la web"""
        if not self._init_core():
            await update.message.reply_text("Saturday no esta listo. Intenta en unos segundos.")
            return
        
        chat_id = update.effective_chat.id
        session_id = self._get_session_id(chat_id)
        user_message = update.message.text
        
        logger.info(f"Mensaje de {chat_id}: {user_message}")
        
        try:
            # Usar process_via_router - mismo pipeline que la web
            result = self.core.process_via_router(user_message, session_id=session_id)
            response = result.get('response', 'No pude procesar eso.')
            
            # Verificar si hay URL para abrir (como el flujo de correos)
            if result.get('navigate_url'):
                response += f"\n\n{result['navigate_url']}"
            
            await update.message.reply_text(response)
            
            # Enviar voz si esta disponible
            if self.core.voice and len(response) < 500:
                try:
                    await self._send_voice(update, context, response)
                except Exception as e:
                    logger.warning(f"No se pudo enviar voz: {e}")
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de voz"""
        if not self._init_core():
            await update.message.reply_text("Saturday no esta listo.")
            return
        
        await update.message.reply_text("Procesando audio...")
        
        try:
            voice = update.message.voice
            file = await context.bot.get_file(voice.file_id)
            
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
                await file.download_to_drive(tmp.name)
                tmp_path = tmp.name
            
            wav_path = tmp_path.replace('.ogg', '.wav')
            subprocess.run(['ffmpeg', '-i', tmp_path, '-ar', '16000', '-ac', '1', wav_path, '-y'], 
                         capture_output=True, check=True)
            
            if self.core.voice:
                transcription = self.core.voice.recognize_audio_file(wav_path)
                if transcription:
                    await update.message.reply_text(f"Escuche: {transcription}")
                    
                    # Procesar la transcripcion con el router
                    chat_id = update.effective_chat.id
                    session_id = self._get_session_id(chat_id)
                    result = self.core.process_via_router(transcription, session_id=session_id)
                    response = result.get('response', 'No pude procesar eso.')
                    await update.message.reply_text(response)
                else:
                    await update.message.reply_text("No pude entender el audio. Intenta de nuevo.")
            else:
                await update.message.reply_text("STT no disponible.")
            
            os.unlink(tmp_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
                
        except Exception as e:
            logger.error(f"Error procesando voz: {e}")
            await update.message.reply_text(f"Error procesando audio: {str(e)}")
    
    async def _send_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Genera y envia un mensaje de voz"""
        import tempfile
        import subprocess
        
        audio_data = self.core.voice._synthesize_google_tts(text)
        if not audio_data:
            return
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            ogg_path = tmp_path.replace('.mp3', '.ogg')
            subprocess.run([
                '/usr/bin/ffmpeg', '-i', tmp_path, '-c:a', 'libopus', '-b:a', '32k', 
                '-application', 'voip', '-vbr', 'on', ogg_path, '-y'
            ], capture_output=True, check=True)
            
            with open(ogg_path, 'rb') as audio_file:
                await context.bot.send_voice(
                    chat_id=update.effective_chat.id,
                    voice=audio_file
                )
            
            os.unlink(tmp_path)
            if os.path.exists(ogg_path):
                os.unlink(ogg_path)
                
        except Exception as e:
            logger.error(f"Error enviando voz: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def send_message(self, text: str, chat_id: int = None):
        """Envia un mensaje proactivamente"""
        if not self.application:
            return
        
        target_chat = chat_id or (next(iter(self._chat_sessions.keys())) if self._chat_sessions else None)
        if not target_chat:
            return
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._send_async(target_chat, text))
            else:
                loop.run_until_complete(self._send_async(target_chat, text))
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
    
    async def _send_async(self, chat_id: int, text: str):
        """Envio asincrono"""
        try:
            await self.application.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Error en envio async: {e}")
    
    def run(self):
        """Inicia el bot"""
        if not self.token:
            return
        
        if not self._init_core():
            logger.error("No se pudo inicializar SaturdayCore")
            return
        
        self.application = (
            Application.builder()
            .token(self.token)
            .read_timeout(30)
            .write_timeout(30)
            .connect_timeout(30)
            .build()
        )
        
        # Handlers - Sin botones, solo texto
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("ayuda", self.cmd_help))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Bot de Telegram iniciado con polling...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )


def main():
    bot = SaturdayTelegramBot()
    bot.run()


if __name__ == '__main__':
    main()