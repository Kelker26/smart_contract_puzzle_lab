#!/usr/bin/env python3
from bot.handlers import PUZZLES, PUZZLES_BY_DIFFICULTY

print("=" * 50)
print("PUZZLE COUNT DIAGNOSTIC")
print("=" * 50)

# Total count
total = len(PUZZLES)
print(f"\n📊 Total Puzzles: {total}")

# By difficulty
for diff in ['Beginner', 'Intermediate', 'Advanced']:
    count = len(PUZZLES_BY_DIFFICULTY[diff])
    print(f"   {diff}: {count}")

# Check expected vs actual
print(f"\n✅ Expected: 33 puzzles (with Ethernaut)")
print(f"📍 Actual: {total} puzzles")

if total == 33:
    print("✓ PERFECT! All puzzles present!")
elif total == 23:
    print("⚠ WARNING: Ethernaut puzzles missing!")
    print("   You have only the base 23 puzzles.")
else:
    print(f"⚠ UNEXPECTED: Got {total} puzzles")

# List all puzzle IDs
print("\n" + "=" * 50)
print("ALL PUZZLE IDs:")
print("=" * 50)

for diff in ['Beginner', 'Intermediate', 'Advanced']:
    print(f"\n{diff}:")
    for pid in sorted(PUZZLES_BY_DIFFICULTY[diff]):
        print(f"  - {pid}")

# Check for Ethernaut
ethernaut_count = len([p for p in PUZZLES.keys() if p.startswith('ethernaut_')])
print(f"\n🎮 Ethernaut puzzles found: {ethernaut_count}")

if ethernaut_count == 10:
    print("✓ All Ethernaut puzzles present!")
elif ethernaut_count == 0:
    print("✗ No Ethernaut puzzles found!")
else:
    print(f"⚠ Only {ethernaut_count}/10 Ethernaut puzzles found!")
