#!/bin/bash

# Smart Contract Puzzle Bot - Automated Setup Script
# This script automates the entire deployment process

set -e  # Exit on any error

echo "🚀 Smart Contract Puzzle Bot - Automated Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed. Please install pip3.${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} pip3 found"

# Check if git is installed (optional but recommended)
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓${NC} git found"
else
    echo -e "${YELLOW}⚠${NC} git not found (optional)"
fi

echo ""

# Create project structure
echo "📁 Creating project structure..."
mkdir -p bot
touch bot/__init__.py

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Telegram Bot Token - Get from @BotFather
TELEGRAM_TOKEN=YOUR_BOT_TOKEN_HERE

# Optional: Database configuration
# DATABASE_URL=postgresql://user:password@localhost/puzzle_db

# Optional: Blockchain integration (future use)
# REWARD_CONTRACT_ADDRESS=
# NFT_CONTRACT_ADDRESS=
EOF
    echo -e "${GREEN}✓${NC} .env file created"
    echo -e "${YELLOW}⚠ Please edit .env and add your Telegram bot token${NC}"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "📝 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
python-telegram-bot==20.7
python-dotenv==1.0.0
EOF
    echo -e "${GREEN}✓${NC} requirements.txt created"
else
    echo -e "${GREEN}✓${NC} requirements.txt already exists"
fi

# Create virtual environment
echo ""
echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo -e "${GREEN}✓${NC} All dependencies installed"

# Check if bot files exist
echo ""
echo "📄 Checking bot files..."

REQUIRED_FILES=("bot/main.py" "bot/handlers.py" "bot/storage.py" "bot/config.py")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    else
        echo -e "${GREEN}✓${NC} $file found"
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please make sure all bot files are in place before running."
    exit 1
fi

# Create a systemd service file (optional, for Linux servers)
echo ""
read -p "📋 Do you want to create a systemd service file? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SERVICE_FILE="puzzle-bot.service"
    CURRENT_DIR=$(pwd)
    USER=$(whoami)
    
    cat > $SERVICE_FILE << EOF
[Unit]
Description=Smart Contract Puzzle Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo -e "${GREEN}✓${NC} Service file created: $SERVICE_FILE"
    echo ""
    echo "To install the service, run:"
    echo "  sudo cp $SERVICE_FILE /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable puzzle-bot"
    echo "  sudo systemctl start puzzle-bot"
fi

# Create run script
echo ""
echo "📝 Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python3 -m bot.main
EOF
chmod +x run.sh
echo -e "${GREEN}✓${NC} run.sh created"

# Create stop script
cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping puzzle bot..."
pkill -f "python3 -m bot.main"
echo "Bot stopped."
EOF
chmod +x stop.sh
echo -e "${GREEN}✓${NC} stop.sh created"

# Create restart script
cat > restart.sh << 'EOF'
#!/bin/bash
echo "Restarting puzzle bot..."
./stop.sh
sleep 2
./run.sh
EOF
chmod +x restart.sh
echo -e "${GREEN}✓${NC} restart.sh created"

# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "user_data.json" ]; then
    cp user_data.json "$BACKUP_DIR/user_data_$TIMESTAMP.json"
    echo "✓ Backup created: $BACKUP_DIR/user_data_$TIMESTAMP.json"
else
    echo "⚠ No user_data.json found to backup"
fi
EOF
chmod +x backup.sh
echo -e "${GREEN}✓${NC} backup.sh created"

# Create stats script
cat > stats.py << 'EOF'
#!/usr/bin/env python3
"""Quick stats viewer for the puzzle bot."""

from bot.storage import load_data, get_stats

def main():
    print("📊 Smart Contract Puzzle Bot - Statistics")
    print("=" * 50)
    
    stats = get_stats()
    print(f"\n📈 Overall Stats:")
    print(f"   Total Users: {stats['total_users']}")
    print(f"   Total Solves: {stats['total_solves']}")
    print(f"   Most Popular: {stats['most_solved_puzzle']} ({stats['most_solved_count']} solves)")
    
    data = load_data()
    print(f"\n👥 User Breakdown:")
    for uid, user in data.items():
        name = user.get('name', 'Unknown')
        score = user.get('score', 0)
        solved = len(user.get('solved', []))
        stage = user.get('stage', 1)
        awards = len(user.get('awards', []))
        print(f"   {name}:")
        print(f"      Score: {score} | Solved: {solved} | Stage: {stage} | Awards: {awards}")

if __name__ == '__main__':
    main()
EOF
chmod +x stats.py
echo -e "${GREEN}✓${NC} stats.py created"

# Check if token is set
echo ""
echo "🔑 Checking bot token..."
if grep -q "YOUR_BOT_TOKEN_HERE" .env; then
    echo -e "${YELLOW}⚠ Bot token not set!${NC}"
    echo ""
    echo "To get your bot token:"
    echo "  1. Open Telegram and search for @BotFather"
    echo "  2. Send /newbot and follow the instructions"
    echo "  3. Copy the token you receive"
    echo "  4. Edit .env file and replace YOUR_BOT_TOKEN_HERE with your token"
    echo ""
    read -p "Press Enter to edit .env now (or Ctrl+C to exit)..."
    ${EDITOR:-nano} .env
else
    echo -e "${GREEN}✓${NC} Bot token is configured"
fi

# Final summary
echo ""
echo "=" * 50
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=" * 50
echo ""
echo "📋 What's been created:"
echo "   ✓ Virtual environment (venv/)"
echo "   ✓ Dependencies installed"
echo "   ✓ Configuration files (.env)"
echo "   ✓ Helper scripts (run.sh, stop.sh, restart.sh, backup.sh)"
echo "   ✓ Stats viewer (stats.py)"
echo ""
echo "🚀 To start the bot:"
echo "   ./run.sh"
echo ""
echo "📊 To view statistics:"
echo "   ./stats.py"
echo ""
echo "💾 To backup user data:"
echo "   ./backup.sh"
echo ""
echo "🔄 To restart the bot:"
echo "   ./restart.sh"
echo ""
echo "🛑 To stop the bot:"
echo "   ./stop.sh"
echo ""
echo "📝 Important files:"
echo "   - .env (your bot token)"
echo "   - user_data.json (auto-created, stores all user data)"
echo "   - backups/ (backup directory)"
echo ""
echo -e "${YELLOW}⚠ Remember to:${NC}"
echo "   1. Make sure your bot token is in .env"
echo "   2. Test with /start in Telegram"
echo "   3. Backup user_data.json regularly"
echo ""
echo "Happy puzzling! 🧩"