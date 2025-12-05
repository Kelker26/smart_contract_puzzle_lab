import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from bot.database import get_connection

MIGRATION_MODE = os.getenv("MIGRATION_MODE") == "1"


def safe_import_handlers():
    if MIGRATION_MODE:
        return {}, {}
    try:
        from bot.handlers import PUZZLES, PUZZLES_BY_DIFFICULTY
        return PUZZLES, PUZZLES_BY_DIFFICULTY
    except:
        return {}, {}


# ---------- SAFE DB WRAPPER ----------

def safe_query(query, params=None, fetchone=False, fetchall=False):
    conn = get_connection()
    if conn is None:
        return None

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or ())

        result = None
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()

        conn.commit()
        cur.close()
        conn.close()
        return result

    except psycopg2.Error as e:
        print(f"⚠ DB Error: {e}")
        return None


# ---------- USERNAME ----------

def set_username(user_id, username):
    safe_query("""
        INSERT INTO users (telegram_id, username)
        VALUES (%s, %s)
        ON CONFLICT (telegram_id)
        DO UPDATE SET username = EXCLUDED.username
    """, (user_id, username))


def get_username(user_id):
    row = safe_query(
        "SELECT username FROM users WHERE telegram_id = %s",
        (user_id,),
        fetchone=True
    )
    return row['username'] if row else None


# ---------- PUZZLE SOLVES ----------

def mark_puzzle_solved(user_id, puzzle_id, correct=True):
    if not correct:
        return

    PUZZLES, _ = safe_import_handlers()

    # Already solved?
    existing = safe_query("""
        SELECT 1 FROM solved_puzzles
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id), fetchone=True)
    
    if existing:
        return

    puzzle = PUZZLES.get(puzzle_id, {})
    points = puzzle.get("points", 10)
    difficulty = puzzle.get("difficulty", "Beginner")

    safe_query("""
        INSERT INTO solved_puzzles (telegram_id, puzzle_id)
        VALUES (%s, %s)
    """, (user_id, puzzle_id))

    safe_query("""
        UPDATE users SET score = score + %s, last_solve_time = CURRENT_TIMESTAMP
        WHERE telegram_id = %s
    """, (points, user_id))

    safe_query("""
        INSERT INTO difficulty_scores (telegram_id, difficulty, score)
        VALUES (%s, %s, %s)
        ON CONFLICT (telegram_id, difficulty)
        DO UPDATE SET score = difficulty_scores.score + EXCLUDED.score
    """, (user_id, difficulty, points))

    wrong_count = safe_query("""
        SELECT COUNT(*) AS c FROM wrong_answers
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id), fetchone=True)

    if wrong_count and wrong_count.get("c") == 0:
        safe_query("""
            INSERT INTO perfect_solves (telegram_id, puzzle_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (user_id, puzzle_id))


def record_wrong_answer(user_id, puzzle_id, answer_text):
    safe_query("""
        INSERT INTO wrong_answers (telegram_id, puzzle_id, answer_text)
        VALUES (%s, %s, %s)
    """, (user_id, puzzle_id, answer_text))


def get_last_wrong(user_id, puzzle_id):
    row = safe_query("""
        SELECT answer_text FROM wrong_answers
        WHERE telegram_id = %s AND puzzle_id = %s
        ORDER BY attempt_time DESC
        LIMIT 1
    """, (user_id, puzzle_id), fetchone=True)

    return row['answer_text'] if row else None


# ---------- PROGRESS ----------

def get_user_progress(user_id):
    user = safe_query(
        "SELECT username, score FROM users WHERE telegram_id = %s",
        (user_id,), fetchone=True
    )
    if not user:
        return [], 0, {}, None

    solved_rows = safe_query(
        "SELECT puzzle_id FROM solved_puzzles WHERE telegram_id = %s",
        (user_id,), fetchall=True
    ) or []
    solved = [r['puzzle_id'] for r in solved_rows]

    diff_rows = safe_query(
        "SELECT difficulty, score FROM difficulty_scores WHERE telegram_id = %s",
        (user_id,), fetchall=True
    ) or []

    diff_scores = {r['difficulty']: r['score'] for r in diff_rows}

    return solved, user["score"], diff_scores, user["username"]


def get_user_stage(user_id):
    row = safe_query(
        "SELECT stage FROM users WHERE telegram_id = %s",
        (user_id,), fetchone=True
    )
    return row["stage"] if row else 1


def advance_user_stage(user_id):
    solved_count = len(get_user_progress(user_id)[0])
    current = get_user_stage(user_id)

    new_stage = current
    if solved_count >= 7 and current < 3:
        new_stage = 3
    elif solved_count >= 3 and current < 2:
        new_stage = 2

    if new_stage != current:
        safe_query(
            "UPDATE users SET stage = %s WHERE telegram_id = %s",
            (new_stage, user_id)
        )

    return new_stage


def is_puzzle_solved(user_id, puzzle_id):
    row = safe_query("""
        SELECT 1 FROM solved_puzzles
        WHERE telegram_id = %s AND puzzle_id = %s
    """, (user_id, puzzle_id), fetchone=True)
    return bool(row)


def get_random_unsolved_puzzle(user_id, difficulty):
    _, PUZZLES_BY_DIFFICULTY = safe_import_handlers()
    import random

    solved = get_user_progress(user_id)[0]
    available = PUZZLES_BY_DIFFICULTY.get(difficulty, [])
    unsolved = [p for p in available if p not in solved]

    return random.choice(unsolved) if unsolved else None


# ---------- AWARDS ----------

def record_award(user_id, award_key):
    safe_query("""
        INSERT INTO user_awards (telegram_id, award_key)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, award_key))


def get_user_awards(user_id):
    rows = safe_query("""
        SELECT award_key FROM user_awards WHERE telegram_id = %s
    """, (user_id,), fetchall=True)

    return [r['award_key'] for r in (rows or [])]


def is_award_earned(user_id, award_key):
    return award_key in get_user_awards(user_id)


def get_perfect_solve_count(user_id):
    row = safe_query("""
        SELECT COUNT(*) AS c FROM perfect_solves WHERE telegram_id = %s
    """, (user_id,), fetchone=True)
    return row["c"] if row else 0


def add_bonus_points(user_id, points):
    safe_query("""
        UPDATE users SET score = score + %s
        WHERE telegram_id = %s
    """, (points, user_id))


# ---------- ADMIN ----------

# ---------- ADMIN USER LOOKUP ----------

def get_user_data(user_id=None):
    # Return a single user
    if user_id:
        return safe_query(
            "SELECT * FROM users WHERE telegram_id = %s",
            (user_id,),
            fetchone=True
        )

    # Return ALL users as {telegram_id: user_data}
    rows = safe_query(
        "SELECT * FROM users",
        fetchall=True
    ) or []

    return {row["telegram_id"]: row for row in rows}


def get_stats():
    users = safe_query("SELECT COUNT(*) AS c FROM users", fetchone=True)
    solves = safe_query("SELECT COUNT(*) AS c FROM solved_puzzles", fetchone=True)
    top = safe_query("""
        SELECT puzzle_id, COUNT(*) AS c FROM solved_puzzles
        GROUP BY puzzle_id ORDER BY c DESC LIMIT 1
    """, fetchone=True)

    return {
        "total_users": users["c"] if users else 0,
        "total_solves": solves["c"] if solves else 0,
        "most_solved_puzzle": top["puzzle_id"] if top else None,
        "most_solved_count": top["c"] if top else 0,
    }


def get_leaderboard(top_n=10, difficulty=None):
    if difficulty:
        rows = safe_query("""
            SELECT u.username, ds.score
            FROM users u
            JOIN difficulty_scores ds ON u.telegram_id = ds.telegram_id
            WHERE ds.difficulty = %s
            ORDER BY ds.score DESC
            LIMIT %s
        """, (difficulty, top_n), fetchall=True)
    else:
        rows = safe_query("""
            SELECT username, score FROM users
            ORDER BY score DESC
            LIMIT %s
        """, (top_n,), fetchall=True)

    return [(r["username"], r["score"]) for r in (rows or [])]

def get_session_stats(user_id):
    solved = safe_query("""
        SELECT COUNT(*) AS c FROM solved_puzzles
        WHERE telegram_id = %s
    """, (user_id,), fetchone=True)

    wrong = safe_query("""
        SELECT COUNT(*) AS c FROM wrong_answers
        WHERE telegram_id = %s
    """, (user_id,), fetchone=True)

    total = (solved["c"] if solved else 0) + (wrong["c"] if wrong else 0)

    accuracy = 0
    if total > 0:
        accuracy = round((solved["c"] / total) * 100, 2)

    return {
        "solved": solved["c"] if solved else 0,
        "wrong": wrong["c"] if wrong else 0,
        "accuracy": accuracy,
    }




