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

    match_name TEXT,
    team TEXT,
    league TEXT,
    kickoff TEXT,

    back_odds REAL,
    lay_odds REAL,

    stake REAL,

    commission REAL,

    lay_stake REAL,

    liability REAL,

    qualifying_loss REAL,

    fta_pct REAL,

    ev_pct REAL,

    expected_profit REAL,

    actual_profit REAL,

    result TEXT,

    model_version TEXT,

    created_at TEXT

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

        home_lead_minute INTEGER,

        away_lead_minute INTEGER,

        processed_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS team_stats (
        team TEXT PRIMARY KEY,

        avg_xg REAL,

        avg_xga REAL,

        goals_last5 INTEGER,

        conceded_last5 INTEGER,

        turnaround_pct REAL,

        two_up_leads INTEGER,

        failed_leads INTEGER,

        home_turnaround_pct REAL,

        away_turnaround_pct REAL,

        historical_matches INTEGER,

        historical_two_up INTEGER,

        historical_comebacks INTEGER,

        two_up_trigger_rate REAL,

        historical_turnaround_rate REAL,

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

        is_home INTEGER,

        back_odds REAL,

        lay_odds REAL,

        avg_xg REAL,

        avg_xga REAL,

        goals_last5 INTEGER,

        conceded_last5 INTEGER,

        turnaround_pct REAL,

        two_up_trigger_rate REAL,

        historical_turnaround_rate REAL,

        lead_minute INTEGER,

        max_lead INTEGER,

        opening_back_odds REAL,

        odds_movement REAL,

        red_cards_for INTEGER,

        red_cards_against INTEGER,

        shots_for INTEGER,

        shots_against INTEGER,

        sample_weight REAL,

        full_turnaround INTEGER,

        created_at TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        setting_name TEXT PRIMARY KEY,
        setting_value TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS processed_fixtures (
        fixture_id TEXT PRIMARY KEY,
        processed_at TEXT
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
    default_value=None
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

    if row:
        return row[0]

    return default_value


def save_tracked_bet(
    data
):

    conn = get_db()

    conn.execute(
        """
        INSERT OR REPLACE INTO tracked_bets
        (
            id,

            match_name,
            team,
            league,
            kickoff,

            back_odds,
            lay_odds,

            stake,

            commission,

            lay_stake,

            liability,

            qualifying_loss,

            fta_pct,

            ev_pct,

            expected_profit,

            actual_profit,

            result,

            model_version,

            created_at
        )

        VALUES
        (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        )
        """,
        (
            data["id"],

            data["match_name"],
            data["team"],
            data["league"],
            data["kickoff"],

            data["back_odds"],
            data["lay_odds"],

            data["stake"],

            data["commission"],

            data["lay_stake"],

            data["liability"],

            data["qualifying_loss"],

            data["fta_pct"],

            data["ev_pct"],

            data["expected_profit"],

            data["actual_profit"],

            data["result"],

            data["model_version"],

            data["created_at"]
        )
    )

    conn.commit()
    conn.close()


def get_tracked_bets():

    conn = get_db()

    rows = conn.execute(
        """
        SELECT *
        FROM tracked_bets
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return rows


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


def update_bet_result(
    bet_id,
    result,
    actual_profit
):

    conn = get_db()

    conn.execute(
        """
        UPDATE tracked_bets
        SET

            result = ?,

            actual_profit = ?

        WHERE id = ?
        """,
        (
            result,
            actual_profit,
            bet_id
        )
    )

    conn.commit()
    conn.close()


def update_tracked_bet(
    bet_id,
    stake,
    commission,
    lay_stake,
    liability
):

    conn = get_db()

    conn.execute(
        """
        UPDATE tracked_bets
        SET

            stake = ?,

            commission = ?,

            lay_stake = ?,

            liability = ?

        WHERE id = ?
        """,
        (
            stake,
            commission,
            lay_stake,
            liability,
            bet_id
        )
    )

    conn.commit()
    conn.close()


def get_performance_stats():

    conn = get_db()

    stats = conn.execute(
        """
        SELECT

            COUNT(*),

            COALESCE(
                SUM(expected_profit),
                0
            ),

            COALESCE(
                SUM(actual_profit),
                0
            )

        FROM tracked_bets
        """
    ).fetchone()

    conn.close()

    return stats


if __name__ == "__main__":

    create_tables()

    print(
        "Database ready"
    )


if __name__ == "__main__":

    create_tables()

    print(
        "Database ready"
    )
