from telegram.ext import ApplicationBuilder, CommandHandler

from app.config import config

BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
from app.bot.commands import start, help_command


def create_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    return app