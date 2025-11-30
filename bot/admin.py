import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from bot.storage import load_data

# Load environment variables
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Default to 0 if not set

async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to show full stats."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    from bot.storage import get_stats

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


async def cmd_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to dump raw user data."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    data = load_data()
    message = "Raw user data:\n"
    for user_id, user_info in data.items():
        message += f"{user_id}: {user_info}\n"

    # Telegram has message length limits, so split if necessary
    for chunk in [message[i:i+4000] for i in range(0, len(message), 4000)]:
        await update.message.reply_text(f"```\n{chunk}\n```", parse_mode="Markdown")


async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to get stats for a specific user.
       Usage: /userstats <username>"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("❌ Please provide a username. Usage: /userstats <username>")
        return

    username = context.args[0]
    data = load_data()

    for user_id, user_data in data.items():
        if user_data.get("name") == username:
            message = f"Stats for {username}:\n"
            message += f"Score: {user_data.get('score', 0)}\n"
            message += f"Solved: {len(user_data.get('solved', []))}\n"
            message += f"Stage: {user_data.get('stage', 0)}\n"
            message += f"Awards: {len(user_data.get('awards', []))}\n"
            await update.message.reply_text(message)
            return

    await update.message.reply_text(f"❌ User {username} not found.")



