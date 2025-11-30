import logging
from telegram.ext import ApplicationBuilder
from bot.config import TELEGRAM_TOKEN
from bot.handlers import register_handlers, PUZZLES
from bot.storage import initialize_puzzle_data


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Initialize and run the Telegram bot."""
    # Initialize puzzle data in storage module
    initialize_puzzle_data(PUZZLES)
    logger.info(f"Initialized {len(PUZZLES)} puzzles")
    
    # Build application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Register all handlers
    register_handlers(app)
    logger.info("All handlers registered successfully")
    
    # Start bot
    logger.info("🤖 Smart Contract Puzzle Bot is starting...")
    logger.info("Press Ctrl+C to stop")
    
    app.run_polling()

if __name__ == "__main__":
    main()