import logging
from telegram import Update
from telegram.ext import ContextTypes

from app.services.dividend_service import get_dividend_info, format_dividend_message

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    logger.info("User %s triggered /start", user)
    await update.message.reply_text(
        f"👋 Welcome to Dividend Genie, {user}!\n\n"
        "Your AI assistant for dividends, bonuses, buybacks and more.\n\n"
        "Try: /dividend ITC"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User triggered /help")
    await update.message.reply_text(
        "📖 *Available Commands*\n\n"
        "/start — Welcome message\n"
        "/help — Show this help\n"
        "/dividend <symbol> — Get dividend info\n\n"
        "Example: /dividend ITC",
        parse_mode="Markdown",
    )


async def dividend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /dividend <symbol>\nExample: /dividend ITC"
        )
        return

    symbol = context.args[0].upper()
    logger.info("User requested dividend for: %s", symbol)

    # Send a "please wait" message while fetching
    wait_msg = await update.message.reply_text(f"🔍 Looking up {symbol}...")

    try:
        data = get_dividend_info(symbol)
        message = format_dividend_message(data)
        await wait_msg.edit_text(message, parse_mode="Markdown")
        logger.info("Successfully returned dividend data for %s", symbol)

    except ValueError as e:
        logger.warning("Dividend lookup failed for %s: %s", symbol, e)
        await wait_msg.edit_text(f"❌ {e}")

    except Exception as e:
        logger.error("Unexpected error fetching dividend for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text(
            "⚠️ Something went wrong. Please try again later."
        )
