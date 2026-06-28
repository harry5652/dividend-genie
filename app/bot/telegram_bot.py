from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from app.config import config
from app.bot.commands import (
    start, help_command, dividend, upcoming, upcoming_page_callback,
    bonus, split, stats,
)


def create_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("dividend", dividend))
    app.add_handler(CommandHandler("upcoming", upcoming))
    app.add_handler(CommandHandler("bonus",    bonus))
    app.add_handler(CommandHandler("split",    split))
    app.add_handler(CommandHandler("stats",    stats))

    # Pagination buttons for /upcoming
    app.add_handler(CallbackQueryHandler(upcoming_page_callback, pattern=r"^up\|"))

    return app
