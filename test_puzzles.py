from bot.handlers import PUZZLES

def test_all_puzzles():
    print(f"Total puzzles: {len(PUZZLES)}")
    
    for puzzle_id, puzzle in PUZZLES.items():
        print(f"\nTesting {puzzle_id}:")
        print(f"  Difficulty: {puzzle['difficulty']}")
        print(f"  Points: {puzzle['points']}")
        print(f"  Answer: {puzzle['answer']}")
        
        # Verify required fields
        assert "question" in puzzle
        assert "answer" in puzzle
        assert "explanation" in puzzle
        assert "difficulty" in puzzle
        assert "points" in puzzle
        assert "stage_required" in puzzle
    
    print(f"\n✅ All {len(PUZZLES)} puzzles are valid!")

if __name__ == '__main__':
    test_all_puzzles()