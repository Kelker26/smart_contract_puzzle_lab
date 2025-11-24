import json
import os
import random

DATA_FILE = "user_data.json"

# Points per puzzle (dynamically determined by puzzle difficulty)
PUZZLE_POINTS = {}

# Map puzzle -> difficulty
PUZZLE_DIFFICULTY = {}

# Dynamically populate from handlers.PUZZLES when imported
def initialize_puzzle_data(puzzles_dict):
    """Initialize puzzle points and difficulty mappings from the PUZZLES dict."""
    global PUZZLE_POINTS, PUZZLE_DIFFICULTY
    for puzzle_id, puzzle_data in puzzles_dict.items():
        PUZZLE_POINTS[puzzle_id] = puzzle_data.get("points", 10)
        PUZZLE_DIFFICULTY[puzzle_id] = puzzle_data.get("difficulty", "Beginner")


def load_data():
    """Load user data from disk. Return {} if missing or malformed."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, IOError):
        return {}


def save_data(data):
    """Persist user data to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def ensure_user_entry(data, uid):
    """Ensure structure for a user id string exists; returns the user dict."""
    if uid not in data or not isinstance(data[uid], dict):
        data[uid] = {
            "name": None,
            "solved": [],
            "score": 0,
            "difficulty_scores": {},
            "last_wrong": {},
            "wrong_counts": {},  # Track wrong attempts per puzzle
            "stage": 1,
            "awards": [],
            "first_solve_time": None,
            "last_solve_time": None,
            "perfect_solves": [],  # Puzzles solved without wrong answers
            "session_solves": [],  # Track solves in current session
            "session_start": None,
        }
    return data[uid]


def set_username(user_id, username):
    """Set or update username for a user."""
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    user["name"] = username
    save_data(data)


def get_username(user_id):
    """Get username for a user."""
    data = load_data()
    uid = str(user_id)
    return data.get(uid, {}).get("name")


def mark_puzzle_solved(user_id, puzzle, correct=True):
    """
    Mark puzzle as solved and award points if correct.
    Only records first solve for each puzzle.
    Tracks perfect solves (no wrong attempts).
    """
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    
    # Only count if not already solved
    if puzzle not in user["solved"]:
        user["solved"].append(puzzle)
        
        if correct:
            points = PUZZLE_POINTS.get(puzzle, 10)
            user["score"] = user.get("score", 0) + points
            
            # Track difficulty scores
            diff = PUZZLE_DIFFICULTY.get(puzzle, "Unknown")
            ds = user.get("difficulty_scores", {})
            ds[diff] = ds.get(diff, 0) + points
            user["difficulty_scores"] = ds
            
            # Update solve timestamps
            import time
            current_time = time.time()
            if user.get("first_solve_time") is None:
                user["first_solve_time"] = current_time
                user["session_start"] = current_time
            user["last_solve_time"] = current_time
            
            # Track perfect solves (no wrong attempts)
            wrong_count = user.get("wrong_counts", {}).get(puzzle, 0)
            if wrong_count == 0:
                perfect_solves = user.get("perfect_solves", [])
                perfect_solves.append(puzzle)
                user["perfect_solves"] = perfect_solves
            
            # Track session solves
            session_solves = user.get("session_solves", [])
            session_solves.append({"puzzle": puzzle, "time": current_time})
            user["session_solves"] = session_solves
    
    save_data(data)


def record_wrong_answer(user_id, puzzle, answer_text):
    """Store the user's last wrong answer for a puzzle."""
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    last_wrong = user.get("last_wrong", {})
    last_wrong[puzzle] = answer_text
    user["last_wrong"] = last_wrong
    save_data(data)


def get_last_wrong(user_id, puzzle):
    """Get user's last wrong answer for a puzzle."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    return user.get("last_wrong", {}).get(puzzle)


def get_user_progress(user_id):
    """
    Return (solved_list, total_score, difficulty_scores_dict, name)
    """
    data = load_data()
    uid = str(user_id)
    user = data.get(uid)
    if not user or not isinstance(user, dict):
        return [], 0, {}, None
    return (
        user.get("solved", []),
        user.get("score", 0),
        user.get("difficulty_scores", {}),
        user.get("name")
    )


def get_user_stage(user_id):
    """Get current stage/level for user."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid)
    if not user:
        return 1
    return user.get("stage", 1)


def advance_user_stage(user_id):
    """
    Check if user should advance to next stage based on puzzles solved.
    Returns new stage number.
    """
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    
    solved_count = len(user.get("solved", []))
    current_stage = user.get("stage", 1)
    
    # Stage advancement logic (updated thresholds)
    new_stage = current_stage
    if solved_count >= 7 and current_stage < 3:
        new_stage = 3
    elif solved_count >= 3 and current_stage < 2:
        new_stage = 2
    
    if new_stage > current_stage:
        user["stage"] = new_stage
        save_data(data)
    
    return new_stage


def get_leaderboard(top_n=10, difficulty=None):
    """
    Return list [(display_name, score), ...] sorted desc.
    If difficulty is provided, return scores for that difficulty only.
    """
    data = load_data()
    results = []
    
    for uid, info in data.items():
        if not isinstance(info, dict):
            continue
        
        if difficulty:
            score = info.get("difficulty_scores", {}).get(difficulty, 0)
        else:
            score = info.get("score", 0)
        
        name = info.get("name") or f"Player_{str(uid)[-4:]}"
        results.append((name, score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def is_puzzle_solved(user_id, puzzle_id):
    """Check if user has solved a specific puzzle."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    return puzzle_id in user.get("solved", [])


def get_random_unsolved_puzzle(user_id, difficulty):
    """
    Get a random unsolved puzzle for the given difficulty.
    Returns puzzle_id or None if all solved.
    """
    from bot.handlers import PUZZLES_BY_DIFFICULTY
    
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    solved = user.get("solved", [])
    
    # Get all puzzles for this difficulty
    available_puzzles = PUZZLES_BY_DIFFICULTY.get(difficulty, [])
    
    # Filter out solved ones
    unsolved = [p for p in available_puzzles if p not in solved]
    
    if not unsolved:
        return None
    
    return random.choice(unsolved)


def record_award(user_id, award_key):
    """Record an award/achievement for a user."""
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    
    awards = user.get("awards", [])
    if award_key not in awards:
        awards.append(award_key)
        user["awards"] = awards
        save_data(data)


def get_user_awards(user_id):
    """Get list of awards earned by user."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    return user.get("awards", [])


def check_and_award_achievements(user_id):
    """
    Check if user has earned any new achievements.
    Returns list of newly earned award keys.
    """
    from bot.handlers import PUZZLES_BY_DIFFICULTY
    
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    
    solved = user.get("solved", [])
    current_awards = user.get("awards", [])
    new_awards = []
    
    # Check first solve
    if len(solved) >= 1 and "first_solve" not in current_awards:
        new_awards.append("first_solve")
    
    # Check difficulty mastery
    for difficulty in ["Beginner", "Intermediate", "Advanced"]:
        award_key = f"{difficulty.lower()}_master"
        if award_key not in current_awards:
            difficulty_puzzles = PUZZLES_BY_DIFFICULTY.get(difficulty, [])
            difficulty_solved = [p for p in solved if p in difficulty_puzzles]
            if len(difficulty_solved) == len(difficulty_puzzles) and len(difficulty_puzzles) > 0:
                new_awards.append(award_key)
    
    # Check grand master (all puzzles)
    from bot.handlers import PUZZLES
    if len(solved) == len(PUZZLES) and "grand_master" not in current_awards:
        new_awards.append("grand_master")
    
    # Record new awards
    for award in new_awards:
        record_award(user_id, award)
    
    return new_awards


def get_stats():
    """Get overall platform statistics."""
    data = load_data()
    
    total_users = len(data)
    total_solves = sum(len(user.get("solved", [])) for user in data.values() if isinstance(user, dict))
    
    # Most solved puzzle
    puzzle_solve_counts = {}
    for user in data.values():
        if isinstance(user, dict):
            for puzzle in user.get("solved", []):
                puzzle_solve_counts[puzzle] = puzzle_solve_counts.get(puzzle, 0) + 1
    
    most_solved = max(puzzle_solve_counts.items(), key=lambda x: x[1]) if puzzle_solve_counts else (None, 0)
    
    return {
        "total_users": total_users,
        "total_solves": total_solves,
        "most_solved_puzzle": most_solved[0],
        "most_solved_count": most_solved[1],
    }


def get_perfect_solve_count(user_id):
    """Get count of puzzles solved without wrong answers."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    return len(user.get("perfect_solves", []))


def is_award_earned(user_id, award_key):
    """Check if user has already earned an award."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    return award_key in user.get("awards", [])


def add_bonus_points(user_id, points):
    """Add bonus points to user's score."""
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    user["score"] = user.get("score", 0) + points
    save_data(data)


def get_session_stats(user_id):
    """Get statistics about current solving session."""
    data = load_data()
    uid = str(user_id)
    user = data.get(uid, {})
    
    session_solves = user.get("session_solves", [])
    if not session_solves:
        return {"count": 0, "duration": 0}
    
    import time
    session_start = user.get("session_start", time.time())
    session_duration = time.time() - session_start
    
    return {
        "count": len(session_solves),
        "duration": session_duration,
        "puzzles": [s["puzzle"] for s in session_solves]
    }


def reset_session(user_id):
    """Reset session tracking for a new session."""
    data = load_data()
    uid = str(user_id)
    user = ensure_user_entry(data, uid)
    
    import time
    user["session_solves"] = []
    user["session_start"] = time.time()
    save_data(data)