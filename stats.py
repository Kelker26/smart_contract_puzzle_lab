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
