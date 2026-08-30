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

        full_turnaround INTEGER,

        created_at TEXT
    )
    """)
