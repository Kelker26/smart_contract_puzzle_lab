"""Database storage implementation - replaces JSON file storage."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from bot.database import get_connection
from datetime import datetime

# Detect migration mode
MIGRATION_MODE = os.getenv("MIGRATION_MODE") == "1"


def safe_import_handlers():
    """Import puzzle handlers, but skip during migration."""
    if MIGRATION_MODE:
        return {}, {}
    try:
        from bot.handlers import PUZZLES, PUZZLES_BY_DIFFICULTY
        return PUZZLES, PUZZLES_BY_DIFFICULTY
    except ImportError:
        return {}, {}


def set_username(user_id, username):
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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT username FROM users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result['username'] if result else None


def mark_puzzle_solved(user_id, puzzle_id, correct=True):
    if not correct:
        return

    PUZZLES, _ = safe_import_handlers()

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT 1 FROM solved_puzzles 
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id))

    if cur.fetchone():
        cur.close()
        conn.close()
        return

    puzzle = PUZZLES.get(puzzle_id, {})
    points = puzzle.get('points', 10)
    difficulty = puzzle.get('difficulty', 'Beginner')

    cur.execute("""
        INSERT INTO solved_puzzles (telegram_id, puzzle_id)
        VALUES (%s, %s)
    """, (user_id, puzzle_id))

    cur.execute("""
        UPDATE users 
        SET score = score + %s,
            last_solve_time = CURRENT_TIMESTAMP
        WHERE telegram_id = %s
    """, (points, user_id))

    cur.execute("""
        INSERT INTO difficulty_scores (telegram_id, difficulty, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id, difficulty)
        DO UPDATE SET score = difficulty_scores.score + EXCLUDED.score
    """, (user_id, difficulty, points))

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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT username, score FROM users WHERE telegram_id = %s", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        return [], 0, {}, None

    cur.execute("SELECT puzzle_id FROM solved_puzzles WHERE telegram_id = %s", (user_id,))
    solved = [row['puzzle_id'] for row in cur.fetchall()]

    cur.execute("SELECT difficulty, score FROM difficulty_scores WHERE telegram_id = %s", (user_id,))
    diff_scores = {row['difficulty']: row['score'] for row in cur.fetchall()}

    cur.close()
    conn.close()

    return solved, user['score'], diff_scores, user['username']


def get_user_stage(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT stage FROM users WHERE telegram_id = %s", (user_id,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result['stage'] if result else 1


def advance_user_stage(user_id):
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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT 1 FROM solved_puzzles 
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id))

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result is not None


def get_random_unsolved_puzzle(user_id, difficulty):
    _, PUZZLES_BY_DIFFICULTY = safe_import_handlers()
    import random

    solved = get_user_progress(user_id)[0]
    available = PUZZLES_BY_DIFFICULTY.get(difficulty, [])
    unsolved = [p for p in available if p not in solved]

    return random.choice(unsolved) if unsolved else None


def record_award(user_id, award_key):
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
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT award_key FROM user_awards WHERE telegram_id = %s
    """, (user_id,))

    awards = [row['award_key'] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return awards


def is_award_earned(user_id, award_key):
    return award_key in get_user_awards(user_id)


def get_perfect_solve_count(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT COUNT(*) as count FROM perfect_solves WHERE telegram_id = %s
    """, (user_id,))

    result = cur.fetchone()

    cur.close()
    conn.close()

    return result['count'] if result else 0


def add_bonus_points(user_id, points):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users SET score = score + %s WHERE telegram_id = %s
    """, (points, user_id))

    conn.commit()
    cur.close()
    conn.close()


def get_session_stats(user_id):
    return {"count": 0, "duration": 0}


def get_stats():
    """Aggregate stats for admin."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cur.fetchone()['total_users']

    cur.execute("SELECT COUNT(*) AS total_solves FROM solved_puzzles")
    total_solves = cur.fetchone()['total_solves']

    cur.execute("""
        SELECT puzzle_id, COUNT(*) AS c 
        FROM solved_puzzles 
        GROUP BY puzzle_id 
        ORDER BY c DESC 
        LIMIT 1
    """)
    row = cur.fetchone()

    most_solved_puzzle = row['puzzle_id'] if row else None
    most_solved_count = row['c'] if row else 0

    cur.close()
    conn.close()

    return {
        "total_users": total_users,
        "total_solves": total_solves,
        "most_solved_puzzle": most_solved_puzzle,
        "most_solved_count": most_solved_count,
    }


def get_user_data(user_id=None):
    """
    If user_id supplied → return single user.
    If none → return all users (dict).
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if user_id:
        cur.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user

    cur.execute("SELECT * FROM users")
    users = {row['telegram_id']: row for row in cur.fetchall()}

    cur.close()
    conn.close()

    return users


# ================= Admin function required by handlers =================
def get_leaderboard(top_n=10, difficulty=None):
    """Return top users by total score or difficulty score."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

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

    results = [(row['username'], row['score']) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return results


