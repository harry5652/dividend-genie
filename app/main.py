from app.bot.telegram_bot import create_bot

bot = create_bot()

print("🚀 Dividend Genie is running...")

bot.run_polling()