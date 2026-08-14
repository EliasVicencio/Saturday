# modules/telegram_bot.py - Versión MVP
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)


class TelegramBot:
    """Bot de Telegram para Saturday - MVP"""
    
    def __init__(self, core, token: str = None):
        self.core = core
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.application = None
        self._chat_id = None
        
        if not self.token:
            print("❌ TELEGRAM_BOT_TOKEN no configurado")
            return
        
        print("🤖 Inicializando bot de Telegram...")
        try:
            self.application = Application.builder().token(self.token).build()
            self._setup_handlers()
            print("✅ Bot de Telegram inicializado")
        except Exception as e:
            print(f"⚠️ Error inicializando Telegram: {e}")
    
    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._chat_id = update.effective_chat.id
        await update.message.reply_text(
            "🤖 ¡Hola! Soy Saturday, tu asistente personal.\n\n"
            "Puedes pedirme:\n"
            "📋 tareas - Ver tareas pendientes\n"
            "📝 crear tarea [nombre] - Crear tarea\n"
            "✅ completar tarea [nombre] - Completar tarea\n"
            "🕐 hora - Hora actual\n"
            "🌤️ clima - Clima\n"
            "❓ ayuda - Más comandos"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self._chat_id = update.effective_chat.id
        user_message = update.message.text
        
        try:
            result = self.core.process_intent(user_message)
            await update.message.reply_text(result['response'])
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    def send_message(self, text: str):
        """Envía un mensaje al chat de Telegram"""
        if self.application and self._chat_id:
            try:
                self.application.bot.send_message(chat_id=self._chat_id, text=text)
            except Exception as e:
                print(f"⚠️ Error enviando a Telegram: {e}")
    
    def run(self):
        if self.application:
            print("🚀 Bot de Telegram iniciado...")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)