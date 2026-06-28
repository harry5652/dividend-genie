import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.services.dividend_service import get_dividend_info, format_dividend_message
from app.services.nse_service import get_upcoming_corporate_actions

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    logger.info("/start from %s", user)
    await update.message.reply_text(
        f"👋 Welcome to Dividend Genie, {user}!\n\n"
        "Your assistant for NSE, BSE & global dividend stocks.\n\n"
        "Commands:\n"
        "  /dividend ITC — dividend info\n"
        "  /dividend ITC 100 — payout for 100 shares\n"
        "  /upcoming — dividends due in 30 days\n"
        "  /help — full guide"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/help requested")
    await update.message.reply_text(
        "📖 *Available Commands*\n\n"
        "/dividend `<symbol>` — Full dividend info\n"
        "/dividend `<symbol>` `<shares>` — With estimated payout\n"
        "/upcoming — Upcoming dividends in next 30 days\n\n"
        "*Exchange suffixes:*\n"
        "  `.NS` → NSE    `.BO` → BSE\n"
        "  No suffix → auto\\-detect (tries NSE then BSE)\n\n"
        "*Examples:*\n"
        "  `/dividend ITC`\n"
        "  `/dividend ITC 500`\n"
        "  `/dividend RELIANCE.NS 100`\n"
        "  `/dividend HDFCBANK.BO`\n"
        "  `/dividend AAPL`",
        parse_mode="Markdown",
    )


async def dividend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "  /dividend ITC\n"
            "  /dividend ITC 100   ← add shares for payout estimate"
        )
        return

    symbol = context.args[0].upper()
    shares = None

    if len(context.args) >= 2:
        try:
            shares = int(context.args[1].replace(",", ""))
            if shares <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Shares must be a positive number. E.g. /dividend ITC 100")
            return

    logger.info("Dividend lookup: symbol=%s shares=%s", symbol, shares)
    wait_msg = await update.message.reply_text(
        f"🔍 Looking up *{symbol}*...", parse_mode="Markdown"
    )

    try:
        data = get_dividend_info(symbol, shares=shares)
        msg  = format_dividend_message(data)
        await wait_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

    except ValueError as e:
        logger.warning("Lookup failed %s: %s", symbol, e)
        await wait_msg.edit_text(f"❌ {e}")

    except Exception as e:
        logger.error("Error for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text("⚠️ Something went wrong. Check Console logs for details.")


def _format_action_block(i: int, item: dict) -> str:
    """Format one corporate action entry for the /upcoming list."""
    ex_dt  = item["ex_date"].strftime("%d-%b-%Y")
    rec_dt = item["record_date"].strftime("%d-%b-%Y") if item["record_date"] else "N/A"
    header = f"{i}. *{item['company']}* ({item['symbol']})"

    if item["type"] == "DIVIDEND":
        amount = f"₹{item['amount']:.2f}/share" if item.get("amount") else item.get("subject", "N/A")
        detail = f"   💰 Dividend: {amount}"

    elif item["type"] == "BONUS":
        ratio  = item.get("ratio") or "N/A"
        detail = f"   🎁 Bonus Issue: {ratio}"

    else:  # SPLIT
        face   = item.get("face_change")
        ratio  = item.get("ratio")
        if face:
            detail = f"   ✂️ Stock Split: {face}"
        elif ratio:
            detail = f"   ✂️ Stock Split: {ratio}"
        else:
            detail = f"   ✂️ Stock Split"

    return (
        f"{header}\n"
        f"{detail}\n"
        f"   📅 Ex-Date: {ex_dt}\n"
        f"   📋 Record Date: {rec_dt}"
    )


async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/upcoming requested")
    wait_msg = await update.message.reply_text(
        "📅 Fetching upcoming corporate actions from NSE..."
    )

    try:
        items = get_upcoming_corporate_actions(days=30)

        if not items:
            await wait_msg.edit_text(
                "ℹ️ No upcoming dividends, bonus issues, or stock splits found in the next 30 days."
            )
            return

        dividends = [a for a in items if a["type"] == "DIVIDEND"]
        bonuses   = [a for a in items if a["type"] == "BONUS"]
        splits    = [a for a in items if a["type"] == "SPLIT"]

        lines = ["📅 *Upcoming Corporate Actions — Next 30 Days*\n"]

        # ── Dividends ────────────────────────────────────────
        if dividends:
            lines.append(f"💰 *Dividends* ({len(dividends)})")
            for i, item in enumerate(dividends[:10], 1):
                lines.append(_format_action_block(i, item))
            if len(dividends) > 10:
                lines.append(f"_...and {len(dividends) - 10} more dividends._")

        # ── Bonus Issues ─────────────────────────────────────
        if bonuses:
            lines.append(f"\n🎁 *Bonus Issues* ({len(bonuses)})")
            for i, item in enumerate(bonuses[:10], 1):
                lines.append(_format_action_block(i, item))
            if len(bonuses) > 10:
                lines.append(f"_...and {len(bonuses) - 10} more bonus issues._")

        # ── Stock Splits ──────────────────────────────────────
        if splits:
            lines.append(f"\n✂️ *Stock Splits* ({len(splits)})")
            for i, item in enumerate(splits[:10], 1):
                lines.append(_format_action_block(i, item))
            if len(splits) > 10:
                lines.append(f"_...and {len(splits) - 10} more splits._")

        await wait_msg.edit_text("\n\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error("Error in /upcoming: %s", e, exc_info=True)
        await wait_msg.edit_text("⚠️ Could not fetch upcoming actions. Please try again later.")
