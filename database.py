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

        stake REAL,

        lay_stake REAL,

        qualifying_loss REAL,

        ev_status TEXT,

        result TEXT,

        expected_profit REAL,

        actual_profit REAL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS odds_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        timestamp TEXT,

        match_id TEXT,

        kickoff TEXT,

        league TEXT,

        home_team TEXT,

        away_team TEXT,

        selection TEXT,

        bookmaker TEXT,

        exchange_name TEXT,

        back_odds REAL,

        lay_odds REAL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS team_stats (
        team TEXT PRIMARY KEY,

        avg_xg REAL,

        avg_xga REAL,

        goals_last5 INTEGER,

        conceded_last5 INTEGER,

        matches_played INTEGER,

        updated_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        match_id TEXT,

        league TEXT,

        team TEXT,

        back_odds REAL,

        lay_odds REAL,

        home_xg REAL,

        away_xg REAL,

        goals_last5 INTEGER,

        conceded_last5 INTEGER,

        full_turnaround INTEGER
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS match_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        match_id TEXT,

        league TEXT,

        home_team TEXT,

        away_team TEXT,

        final_home INTEGER,

        final_away INTEGER,

        home_2up INTEGER,

        away_2up INTEGER,

        home_turnaround INTEGER,

        away_turnaround INTEGER,

        processed_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        setting_name TEXT PRIMARY KEY,

        setting_value TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_setting(
    name,
    value
):

    conn = get_db()

    conn.execute(
        """
        INSERT OR REPLACE INTO settings
        (
            setting_name,
            setting_value
        )
        VALUES
        (?, ?)
        """,
        (
            name,
            str(value)
        )
    )

    conn.commit()
    conn.close()


def get_setting(
    name,
    default=None
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT setting_value
        FROM settings
        WHERE setting_name = ?
        """,
        (name,)
    ).fetchone()

    conn.close()

    if not row:
        return default

    return row[0]


def save_tracked_bet(item):

    conn = get_db()

    conn.execute(
        """
        INSERT OR REPLACE INTO tracked_bets
        VALUES
        (
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?
        )
        """,
        (
            item["id"],
            item["match"],
            item["team"],
            item["kickoff"],

            item["back_odds"],
            item["lay_odds"],

            item["stake"],
            item["lay_stake"],

            item["qualifying_loss"],

            item["ev_status"],

            item["result"],

            item["expected_profit"],

            item["actual_profit"]
        )
    )

    conn.commit()
    conn.close()


def load_tracked_bets():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM tracked_bets
        """
    ).fetchall()

    conn.close()

    return [
        {
            "id": r[0],
            "match": r[1],
            "team": r[2],
            "kickoff": r[3],
            "back_odds": r[4],
            "lay_odds": r[5],
            "stake": r[6],
            "lay_stake": r[7],
            "qualifying_loss": r[8],
            "ev_status": r[9],
            "result": r[10],
            "expected_profit": r[11],
            "actual_profit": r[12]
        }
        for r in rows
    ]


def delete_tracked_bet(
    bet_id
):

    conn = get_db()

    conn.execute(
        """
        DELETE FROM tracked_bets
        WHERE id = ?
        """,
        (bet_id,)
    )

    conn.commit()
    conn.close()
