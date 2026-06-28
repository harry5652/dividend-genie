import logging
from app.bot.telegram_bot import create_bot

# Configure logging — all output appears in the Console tab
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

bot = create_bot()

logger.info("🚀 Dividend Genie is running...")
print("🚀 Dividend Genie is running...")

bot.run_polling()
