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
        "Your AI assistant for dividends across NSE, BSE, and global markets.\n\n"
        "Examples:\n"
        "  /dividend ITC       — auto-detect (NSE/BSE)\n"
        "  /dividend ITC.NS    — NSE explicitly\n"
        "  /dividend ITC.BO    — BSE explicitly\n"
        "  /dividend AAPL      — US stocks\n\n"
        "Type /help for all commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("User triggered /help")
    await update.message.reply_text(
        "📖 *Available Commands*\n\n"
        "/start — Welcome message\n"
        "/help — Show this help\n"
        "/dividend <symbol> — Get dividend info\n\n"
        "*Exchange suffixes:*\n"
        "  `.NS` → NSE (e.g. ITC.NS)\n"
        "  `.BO` → BSE (e.g. ITC.BO)\n"
        "  No suffix → auto-detect (tries NSE then BSE)\n\n"
        "*Examples:*\n"
        "  /dividend ITC\n"
        "  /dividend RELIANCE.NS\n"
        "  /dividend HDFCBANK.BO\n"
        "  /dividend AAPL",
        parse_mode="Markdown",
    )


async def dividend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /dividend <symbol>\n\n"
            "Examples:\n"
            "  /dividend ITC         (auto NSE/BSE)\n"
            "  /dividend RELIANCE.NS (NSE)\n"
            "  /dividend HDFCBANK.BO (BSE)\n"
            "  /dividend AAPL        (US)"
        )
        return

    symbol = context.args[0].upper()
    logger.info("Dividend requested for: %s", symbol)

    wait_msg = await update.message.reply_text(f"🔍 Looking up *{symbol}*...", parse_mode="Markdown")

    try:
        data = get_dividend_info(symbol)
        message = format_dividend_message(data)
        await wait_msg.edit_text(message, parse_mode="Markdown")
        logger.info("Returned dividend data for %s", symbol)

    except ValueError as e:
        logger.warning("Lookup failed for %s: %s", symbol, e)
        await wait_msg.edit_text(f"❌ {e}")

    except Exception as e:
        logger.error("Unexpected error for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text("⚠️ Something went wrong. Please try again later.")
