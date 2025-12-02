"""Migrate JSON user_data.json into PostgreSQL."""

import os
# IMPORTANT: Enable migration mode BEFORE importing db_storage
os.environ["MIGRATION_MODE"] = "1"

import json
from bot.db_storage import (
    set_username,
    mark_puzzle_solved,
    record_award
)


def main():
    # Load old JSON data
    with open("user_data.json", "r") as f:
        data = json.load(f)

    print(f"📦 Migrating {len(data)} users...")

    for telegram_id_str, user in data.items():
        telegram_id = int(telegram_id_str)

        # 1. Username
        username = user.get("name")
        if username:
            set_username(telegram_id, username)

        # 2. Solved puzzles
        solved = user.get("solved", [])
        for puzzle_id in solved:
            # safe: will not try importing PUZZLES due to MIGRATION_MODE=1
            mark_puzzle_solved(telegram_id, puzzle_id, correct=True)

        # 3. Awards
        awards = user.get("awards", [])
        for award_key in awards:
            record_award(telegram_id, award_key)

        print(f"  ✔ Migrated: {username} ({telegram_id})")

    print("🎉 Migration complete!")


if __name__ == "__main__":
    main()

