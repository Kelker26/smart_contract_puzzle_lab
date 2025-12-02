"""Check migrated users in PostgreSQL."""
from bot.db_storage import get_user_data, get_user_progress

def main():
    users = get_user_data()  # Get all users from DB

    if not users:
        print("⚠️ No users found in the database.")
        return

    print("✅ User check results:")

    for user_id, user in users.items():
        username = user.get('username', 'Unknown')
        score = user.get('score', 0)
        stage = user.get('stage', 1)
        solved_count = len(get_user_progress(user_id)[0])  # Solved puzzles list

        print(f"{username} ({user_id}) - Score: {score}, Stage: {stage}, Solved Puzzles: {solved_count}")


if __name__ == "__main__":
    main()

