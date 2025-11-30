from telegram import Update
from telegram.ext import ContextTypes
from bot.storage import get_stats, load_data

# Telegram ID
ADMIN_ID = 6998310320

async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to show full stats."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    stats = get_stats()
    data = load_data()

    message = f"📈 Overall Stats:\n"
    message += f"   Total Users: {stats['total_users']}\n"
    message += f"   Total Solves: {stats['total_solves']}\n"
    message += f"   Most Popular: {stats['most_solved_puzzle']} ({stats['most_solved_count']} solves)\n\n"
    
    message += "👥 User Breakdown:\n"
    for user_id, user_data in data.items():
        message += f"   {user_data.get('name', 'Unknown')}:\n"
        message += f"      Score: {user_data.get('score', 0)} | "
        message += f"Solved: {len(user_data.get('solved', []))} | "
        message += f"Stage: {user_data.get('stage', 0)} | "
        message += f"Awards: {len(user_data.get('awards', []))}\n"

    await update.message.reply_text(message)

