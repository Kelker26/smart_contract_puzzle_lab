# 🧩 Smart Contract Puzzle Lab - Telegram Bot

A gamified Solidity learning platform with progressive difficulty levels, random puzzle selection, and achievement system.

## ✨ Features

### 🎯 Core Functionality
- **3 Difficulty Levels**: Beginner, Intermediate, Advanced
- **Random Puzzle Selection**: Get unsolved puzzles randomly
- **Multiple Stages**: Progressive unlocking system
  - Stage 1: Beginner (Always unlocked)
  - Stage 2: Intermediate (Unlock after 2 puzzles)
  - Stage 3: Advanced (Unlock after 4 puzzles)
- **Smart Answer Checking**: Flexible answer validation
- **Award System**: Achievements for milestones

### 📊 Tracking & Leaderboards
- **Progress Tracking**: Personal stats by difficulty
- **Leaderboards**: Overall + per-difficulty rankings
- **Achievement Badges**: 6+ awards to unlock
- **Wrong Answer History**: Learn from mistakes

### 🎁 Available Awards
- 🎯 **First Blood**: Solve your first puzzle
- 🟢 **Beginner Master**: Complete all beginner puzzles
- 🟡 **Intermediate Master**: Complete all intermediate puzzles
- 🔴 **Advanced Master**: Complete all advanced puzzles
- 👑 **Grand Master**: Complete ALL puzzles

### 🧩 Puzzle Categories
- **Beginner**: Basic Solidity concepts (4 puzzles)
- **Intermediate**: Mappings, events, security basics (4 puzzles)
- **Advanced**: Real vulnerabilities - reentrancy, delegatecall, tx.origin (5 puzzles)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- A Telegram account

### Installation

1. **Clone the repository**
```bash
git clone <your-repo>
cd smart-contract-puzzle-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create .env file**
```bash
# Create .env in project root
echo "TELEGRAM_TOKEN=your_token_here" > .env
```

4. **Get Telegram Bot Token**
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` command
   - Follow instructions to create your bot
   - Copy the token you receive
   - Paste it in your `.env` file

5. **Run the bot**
```bash
python -m bot.main
```

## 📁 Project Structure

```
smart-contract-puzzle-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── config.py        # Configuration
│   ├── handlers.py      # Command & callback handlers
│   └── storage.py       # Data persistence
├── .env                 # Environment variables (create this)
├── requirements.txt     # Python dependencies
├── user_data.json       # Auto-generated user data
└── README.md
```

## 📦 requirements.txt

```txt
python-telegram-bot==20.7
python-dotenv==1.0.0
```

## 🎮 Bot Commands

- `/start` - Begin your journey
- `/menu` - Open main menu
- `/progress` - View your stats
- `/leaderboard` - See top players

## 🔧 Configuration

### Adding More Puzzles

Edit `handlers.py` and add to the `PUZZLES` dictionary:

```python
"puzzle_id": {
    "question": "Your puzzle question with ```solidity code```",
    "answer": "expected_answer",
    "explanation": "Why this is the answer",
    "difficulty": "Beginner|Intermediate|Advanced",
    "points": 10,  # Points awarded
    "stage_required": 1,  # Minimum stage to access
}
```

### Adjusting Stage Requirements

Modify `STAGE_REQUIREMENTS` in `handlers.py`:

```python
STAGE_REQUIREMENTS = {
    1: 0,   # Stage 1 unlocked by default
    2: 2,   # Unlock after X puzzles
    3: 4,   # Unlock after X puzzles
}
```

### Creating New Awards

Add to `AWARDS` dictionary in `handlers.py`:

```python
"award_key": {
    "name": "🏆 Award Name",
    "description": "How to earn this"
}
```

## 🌐 Future: Web Version

The bot is designed to easily port to a web application:

### Planned Features
- React/Next.js frontend
- REST API backend
- Smart contract integration
- On-chain verification
- NFT/Token rewards
- Real-time leaderboards
- Social features (teams, challenges)

### Architecture Ready for:
- Database migration (PostgreSQL/MongoDB)
- Blockchain integration (ethers.js/web3.py)
- OAuth authentication
- WebSocket for real-time updates

## 🎁 Blockchain Rewards (Coming Soon)

The bot includes infrastructure for blockchain-based rewards:

```python
# In config.py
AWARD_CONFIG = {
    "enable_blockchain_rewards": True,
    "reward_wallet": "0x...",  # Your reward contract
    "nft_contract": "0x...",   # NFT achievement badges
}
```

### Planned Reward System
- **Tokens**: Earn ERC-20 tokens for solving puzzles
- **NFTs**: Unique achievement badges as NFTs
- **Leaderboard Prizes**: Weekly/monthly competitions
- **Staking**: Stake tokens for premium puzzles

## 📊 Data Storage

Currently uses JSON file storage (`user_data.json`). Structure:

```json
{
  "user_id": {
    "name": "username",
    "solved": ["puzzle1", "puzzle2"],
    "score": 100,
    "difficulty_scores": {"Beginner": 50, "Intermediate": 50},
    "stage": 2,
    "awards": ["first_solve", "beginner_master"],
    "last_wrong": {"puzzle3": "wrong_answer"}
  }
}
```

For production, migrate to PostgreSQL/MongoDB using `DATABASE_CONFIG` in `config.py`.

## 🤝 Contributing

Want to add more puzzles or features?

1. Fork the repository
2. Create a feature branch
3. Add your puzzles/features
4. Test thoroughly
5. Submit a pull request

### Puzzle Guidelines
- **Beginner**: Basic syntax, simple concepts
- **Intermediate**: Common patterns, basic security
- **Advanced**: Real vulnerabilities, complex patterns

## 🐛 Troubleshooting

### Bot not responding
- Check your token in `.env`
- Ensure bot is running: `python -m bot.main`
- Check internet connection

### "Module not found" error
```bash
pip install -r requirements.txt
```

### User data corrupted
Delete `user_data.json` (data will be lost) or fix JSON syntax

## 📝 License

MIT License - feel free to use and modify!

## 🙏 Credits

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Solidity security concepts from [Consensys Best Practices](https://consensys.github.io/smart-contract-best-practices/)

---

**Ready to level up your Solidity skills? Start the bot and begin solving! 🚀**