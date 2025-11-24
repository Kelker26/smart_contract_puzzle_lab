# Add this to a new file: check_stats.py
from bot.storage import get_stats, load_data

# Get overall stats
stats = get_stats()
print(f"Total users: {stats['total_users']}")
print(f"Total solves: {stats['total_solves']}")
print(f"Most popular puzzle: {stats['most_solved_puzzle']}")

# Get specific user data
data = load_data()
for user_id, user_data in data.items():
    print(f"\n{user_data.get('name', 'Unknown')}:")
    print(f"  Score: {user_data.get('score', 0)}")
    print(f"  Solved: {len(user_data.get('solved', []))}")
    print(f"  Awards: {len(user_data.get('awards', []))}")