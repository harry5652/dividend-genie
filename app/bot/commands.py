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


async def dividend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /dividend <symbol>\nExample: /dividend ITC")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"Fetching dividend info for {symbol}...")