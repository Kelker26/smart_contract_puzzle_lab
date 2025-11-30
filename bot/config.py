import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token - Get from @BotFather on Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("Environment variable TELEGRAM_TOKEN not found.")


# Award Configuration - Future: Could include wallet addresses for token/NFT rewards
AWARD_CONFIG = {
    "enable_blockchain_rewards": False,  # Set to True when ready to integrate blockchain
    "reward_wallet": None,  # Contract address for reward distribution
    "nft_contract": None,  # NFT contract for achievement badges
}

# API Configuration for future web integration
API_CONFIG = {
    "enable_api": False,
    "api_port": 8080,
    "api_host": "0.0.0.0",
}

# Database configuration (for scaling beyond JSON)
DATABASE_CONFIG = {
    "use_database": False,  # Set to True to use PostgreSQL/MongoDB instead of JSON
    "db_url": os.getenv("DATABASE_URL", None),
}