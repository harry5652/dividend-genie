from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Dividend Genie!\n\nYour AI assistant for dividends, bonuses, buybacks and more."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
Available Commands

/start
/help
/dividend <symbol>

Example:
/dividend ITC
"""
    )