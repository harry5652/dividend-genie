import logging
from app.database.db import init_db
from app.bot.telegram_bot import create_bot

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Initialise DB tables before anything else
init_db()
logger.info("Database initialised.")

bot = create_bot()

logger.info("🚀 Dividend Genie is running...")
print("🚀 Dividend Genie is running...")

bot.run_polling()
