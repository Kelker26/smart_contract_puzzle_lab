import json
from telegram import Update, InputFile
from telegram.ext import ContextTypes

from bot.storage import get_stats, load_data

ADMIN_ID = 6998310320   


def admin_only(func):
    """Decorator to restrict access to admin only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("Access denied.")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    msg = (
        f"📊 Bot Statistics\n"
        f"-----------------\n"
        f"Total users: {stats['total_users']}\n"
        f"Total solves: {stats['total_solves']}\n"
        f"Most solved puzzle: {stats['most_solved_puzzle']}"
    )
    await update.message.reply_text(msg)


@admin_only
async def cmd_dump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the full data.json as a file."""
    data = load_data()
    json_bytes = json.dumps(data, indent=4).encode("utf-8")
    await update.message.reply_document(
        document=InputFile(
            path_or_bytes=json_bytes,
            filename="data.json"
        )
    )


@admin_only
async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check stats for a specific user ID."""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /userstats <telegram_user_id>")
        return

    user_id = context.args[0]
    data = load_data()

    user = data.get(user_id)
    if not user:
        await update.message.reply_text("User not found.")
        return

    msg = (
        f"📌 User: {user.get('name', 'Unknown')}\n"
        f"User ID: {user_id}\n"
        f"Score: {user.get('score', 0)}\n"
        f"Solved puzzles: {len(user.get('solved', []))}\n"
        f"Awards: {len(user.get('awards', []))}"
    )
    await update.message.reply_text(msg)
