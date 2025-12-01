"""Database storage implementation - replaces JSON file storage."""
import psycopg2
from psycopg2.extras import RealDictCursor
from bot.database import get_connection
from datetime import datetime

def set_username(user_id, username):
    """Set or update username."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO users (telegram_id, username)
        VALUES (%s, %s)
        ON CONFLICT (telegram_id) 
        DO UPDATE SET username = EXCLUDED.username
    """, (user_id, username))
    
    conn.commit()
    cur.close()
    conn.close()

def get_username(user_id):
    """Get username."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT username FROM users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result['username'] if result else None

def mark_puzzle_solved(user_id, puzzle_id, correct=True):
    """Mark puzzle as solved and award points."""
    if not correct:
        return
    
    from bot.handlers import PUZZLES
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if already solved
    cur.execute("""
        SELECT 1 FROM solved_puzzles 
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id))
    
    if cur.fetchone():
        cur.close()
        conn.close()
        return  # Already solved
    
    # Get puzzle info
    puzzle = PUZZLES.get(puzzle_id, {})
    points = puzzle.get('points', 10)
    difficulty = puzzle.get('difficulty', 'Beginner')
    
    # Insert solved puzzle
    cur.execute("""
        INSERT INTO solved_puzzles (telegram_id, puzzle_id)
        VALUES (%s, %s)
    """, (user_id, puzzle_id))
    
    # Update user score
    cur.execute("""
        UPDATE users 
        SET score = score + %s,
            last_solve_time = CURRENT_TIMESTAMP
        WHERE telegram_id = %s
    """, (points, user_id))
    
    # Update difficulty score
    cur.execute("""
        INSERT INTO difficulty_scores (telegram_id, difficulty, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id, difficulty)
        DO UPDATE SET score = difficulty_scores.score + EXCLUDED.score
    """, (user_id, difficulty, points))
    
    # Track perfect solve (no wrong answers for this puzzle)
    cur.execute("""
        SELECT COUNT(*) as count FROM wrong_answers
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id))
    
    wrong_count = cur.fetchone()['count']
    if wrong_count == 0:
        cur.execute("""
            INSERT INTO perfect_solves (telegram_id, puzzle_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (user_id, puzzle_id))
    
    conn.commit()
    cur.close()
    conn.close()

def record_wrong_answer(user_id, puzzle_id, answer_text):
    """Record wrong answer attempt."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO wrong_answers (telegram_id, puzzle_id, answer_text)
        VALUES (%s, %s, %s)
    """, (user_id, puzzle_id, answer_text))
    
    conn.commit()
    cur.close()
    conn.close()

def get_last_wrong(user_id, puzzle_id):
    """Get last wrong answer for a puzzle."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT answer_text FROM wrong_answers
        WHERE telegram_id = %s AND puzzle_id = %s
        ORDER BY attempt_time DESC
        LIMIT 1
    """, (user_id, puzzle_id))
    
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result['answer_text'] if result else None

def get_user_progress(user_id):
    """Get user progress: (solved_list, total_score, difficulty_scores, name)."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Get user info
    cur.execute("""
        SELECT username, score FROM users WHERE telegram_id = %s
    """, (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return [], 0, {}, None
    
    # Get solved puzzles
    cur.execute("""
        SELECT puzzle_id FROM solved_puzzles WHERE telegram_id = %s
    """, (user_id,))
    solved = [row['puzzle_id'] for row in cur.fetchall()]
    
    # Get difficulty scores
    cur.execute("""
        SELECT difficulty, score FROM difficulty_scores WHERE telegram_id = %s
    """, (user_id,))
    diff_scores = {row['difficulty']: row['score'] for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    return solved, user['score'], diff_scores, user['username']

def get_user_stage(user_id):
    """Get current stage."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT stage FROM users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result['stage'] if result else 1

def advance_user_stage(user_id):
    """Check and advance user stage based on puzzles solved."""
    solved_count = len(get_user_progress(user_id)[0])
    current_stage = get_user_stage(user_id)
    
    new_stage = current_stage
    if solved_count >= 7 and current_stage < 3:
        new_stage = 3
    elif solved_count >= 3 and current_stage < 2:
        new_stage = 2
    
    if new_stage > current_stage:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users SET stage = %s WHERE telegram_id = %s
        """, (new_stage, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
    
    return new_stage

def is_puzzle_solved(user_id, puzzle_id):
    """Check if puzzle is solved."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 1 FROM solved_puzzles 
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id))
    
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result is not None

def get_random_unsolved_puzzle(user_id, difficulty):
    """Get random unsolved puzzle for difficulty."""
    from bot.handlers import PUZZLES_BY_DIFFICULTY
    import random
    
    solved = get_user_progress(user_id)[0]
    available = PUZZLES_BY_DIFFICULTY.get(difficulty, [])
    unsolved = [p for p in available if p not in solved]
    
    return random.choice(unsolved) if unsolved else None

def record_award(user_id, award_key):
    """Record an award."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO user_awards (telegram_id, award_key)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, award_key))
    
    conn.commit()
    cur.close()
    conn.close()

def get_user_awards(user_id):
    """Get list of awards."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT award_key FROM user_awards WHERE telegram_id = %s
    """, (user_id,))
    
    awards = [row['award_key'] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return awards

def is_award_earned(user_id, award_key):
    """Check if award is earned."""
    return award_key in get_user_awards(user_id)

def get_perfect_solve_count(user_id):
    """Get count of perfect solves."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) as count FROM perfect_solves WHERE telegram_id = %s
    """, (user_id,))
    
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result['count'] if result else 0

def add_bonus_points(user_id, points):
    """Add bonus points to user score."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE users SET score = score + %s WHERE telegram_id = %s
    """, (points, user_id))
    
    conn.commit()
    cur.close()
    conn.close()

def get_session_stats(user_id):
    """Get session statistics."""
    # Simplified for now
    return {"count": 0, "duration": 0}

def get_leaderboard(top_n=10, difficulty=None):
    """Get leaderboard."""
    conn = get_connection()
    cur = conn.cursor()
    
    if difficulty:
        cur.execute("""
            SELECT u.username, ds.score
            FROM users u
            JOIN difficulty_scores ds ON u.telegram_id = ds.telegram_id
            WHERE ds.difficulty = %s
            ORDER BY ds.score DESC
            LIMIT %s
        """, (difficulty, top_n))
    else:
        cur.execute("""
            SELECT username, score
            FROM users
            ORDER BY score DESC
            LIMIT %s
        """, (top_n,))
    
    results = [(row['username'] or f"Player_{row.get('telegram_id', '0000')[-4:]}", 
                row['score']) for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return results
