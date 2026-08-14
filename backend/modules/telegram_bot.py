# modules/telegram_bot.py
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)


class TelegramBot:
    """Bot de Telegram para Saturday"""
    
    def __init__(self, core, token: str = None):
        self.core = core
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.application = None
        
        if not self.token:
            print("❌ TELEGRAM_BOT_TOKEN no configurado")
            return
        
        print("🤖 Inicializando bot de Telegram...")
        self.application = Application.builder().token(self.token).build()
        self._setup_handlers()
        print("✅ Bot de Telegram inicializado")
    
    def _setup_handlers(self):
        """Configura los manejadores"""
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🤖 Saturday conectado. Envía un mensaje y te responderé.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        result = self.core.process_intent(user_message)
        await update.message.reply_text(result['response'])
    
    def send_message(self, text: str):
        """Envía un mensaje al chat de Telegram"""
        # Implementar envío de mensajes
        pass
    
    def run(self):
        if self.application:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)