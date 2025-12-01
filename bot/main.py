import logging
from telegram.ext import ApplicationBuilder
from bot.config import TELEGRAM_TOKEN
from bot.handlers import register_handlers, PUZZLES
from bot.database import init_database

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main():
    """Initialize and run the Telegram bot."""

    # ----------------------------------------------------
    # 1. Initialize PostgreSQL database
    # ----------------------------------------------------
    try:
        init_database()
        logger.info("✅ PostgreSQL database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("⚠ Bot will continue running, but DB operations may fail")

    # ----------------------------------------------------
    # 2. Initialize puzzle list (still needed by handlers)
    # ----------------------------------------------------
    logger.info(f"Loaded {len(PUZZLES)} puzzles")

    # ----------------------------------------------------
    # 3. Build the Telegram bot application
    # ----------------------------------------------------
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ----------------------------------------------------
    # 4. Register all bot command/message handlers
    # ----------------------------------------------------
    register_handlers(app)
    logger.info("All handlers registered successfully")

    # ----------------------------------------------------
    # 5. Start the bot
    # ----------------------------------------------------
    logger.info("🤖 Smart Contract Puzzle Bot is now running...")
    logger.info("Press Ctrl+C to stop the bot")

    app.run_polling()

if __name__ == "__main__":
    main()

