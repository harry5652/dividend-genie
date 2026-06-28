from telegram.ext import ApplicationBuilder, CommandHandler

from app.config import config
from app.bot.commands import start, help_command, dividend, upcoming, bonus, split


def create_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("dividend", dividend))
    app.add_handler(CommandHandler("upcoming", upcoming))
    app.add_handler(CommandHandler("bonus",    bonus))
    app.add_handler(CommandHandler("split",    split))

    return app
