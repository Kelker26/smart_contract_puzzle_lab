import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from bot.db_storage import (
    get_stats,
    get_user_data,
    get_username,
    get_user_progress,
    get_user_awards,
)

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


async def cmd_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    stats = get_stats()

    message = (
        "📈 Overall Stats:\n"
        f"Total Users: {stats['total_users']}\n"
        f"Total Solves: {stats['total_solves']}\n"
        f"Most Solved Puzzle: {stats['most_solved_puzzle']} ({stats['most_solved_count']} solves)"
    )

    await update.message.reply_text(message)


async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /userstats <telegram_id>")
        return

    telegram_id = int(context.args[0])
    user_data = get_user_data(telegram_id)

    if not user_data:
        await update.message.reply_text("❌ User not found.")
        return

    solved, score, diff_scores, username = get_user_progress(telegram_id)
    awards = get_user_awards(telegram_id)

    msg = (
        f"👤 User: {username} (ID: {telegram_id})\n"
        f"Score: {score}\n"
        f"Solved Puzzles: {', '.join(solved)}\n"
        f"Awards: {', '.join(awards)}\n"
        "Difficulty Breakdown:\n"
        + "\n".join(f"  {d}: {p}" for d, p in diff_scores.items())
    )

    await update.message.reply_text(msg)


async def cmd_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    users = get_user_data()
    msg = "🗂 All User Data:\n"

    for uid, user in users.items():
        msg += f"{user.get('username', 'Unknown')} (ID:{uid}) Score={user.get('score', 0)}\n"

    for chunk in [msg[i:i+4000] for i in range(0, len(msg), 4000)]:
        await update.message.reply_text(chunk)





