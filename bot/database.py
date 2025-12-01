import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_database():
    """Initialize database tables."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            username VARCHAR(100),
            score INTEGER DEFAULT 0,
            stage INTEGER DEFAULT 1,
            first_solve_time TIMESTAMP,
            last_solve_time TIMESTAMP,
            session_start TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Solved puzzles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS solved_puzzles (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT REFERENCES users(telegram_id),
            puzzle_id VARCHAR(50),
            solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(telegram_id, puzzle_id)
        )
    """)
    
    # Wrong answers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wrong_answers (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT REFERENCES users(telegram_id),
            puzzle_id VARCHAR(50),
            answer_text TEXT,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Awards table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_awards (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT REFERENCES users(telegram_id),
            award_key VARCHAR(50),
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(telegram_id, award_key)
        )
    """)
    
    # Difficulty scores table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS difficulty_scores (
            telegram_id BIGINT REFERENCES users(telegram_id),
            difficulty VARCHAR(20),
            score INTEGER DEFAULT 0,
            PRIMARY KEY(telegram_id, difficulty)
        )
    """)
    
    # Perfect solves tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS perfect_solves (
            telegram_id BIGINT REFERENCES users(telegram_id),
            puzzle_id VARCHAR(50),
            PRIMARY KEY(telegram_id, puzzle_id)
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_database()
