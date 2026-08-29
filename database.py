import sqlite3

DB_NAME = "two_up.db"


def get_db():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def create_tables():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tracked_bets (
        id TEXT PRIMARY KEY,
        match TEXT,
        team TEXT,
        kickoff TEXT,
        back_odds REAL,
        lay_odds REAL,
        ev_status TEXT,
        result TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS odds_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        match_id TEXT,
        team TEXT,
        back_odds REAL,
        lay_odds REAL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT,
        team TEXT,
        back_odds REAL,
        lay_odds REAL,
        home_xg REAL,
        away_xg REAL,
        full_turnaround INTEGER
    )
    """)

    conn.commit()
    conn.close()
