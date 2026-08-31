import pandas as pd
from datetime import datetime, timezone

from database import get_db


CSV_FILE = "2up_multi_league_dataset.csv"


def import_dataset():

    conn = get_db()

    df = pd.read_csv(
        CSV_FILE
    )

    inserted = 0

    for _, row in df.iterrows():

        triggered = bool(
            row["2up_triggered"]
        )

        comeback = bool(
            row["comeback_occurred"]
        )

        if not triggered:
            continue

        conn.execute(
            """
            INSERT INTO training_data
            (
                match_id,
                league,
                team,

                is_home,

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                lead_minute,
                max_lead,

                opening_back_odds,
                odds_movement,

                red_cards_for,
                red_cards_against,

                shots_for,
                shots_against,

                sample_weight,

                full_turnaround,

                created_at
            )

            VALUES
            (
                ?,?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                f"csv_{inserted}",

                "Historical",

                row["trigger_team"],

                0,

                0,
                0,

                0,
                0,

                0,

                0,
                2,

                0,
                0,

                0,
                0,

                0,
                0,

                0.50,

                int(comeback),

                datetime.now(
                    timezone.utc
                ).isoformat()
            )
        )

        inserted += 1

    conn.commit()
    conn.close()

    print(
        f"{inserted} historical rows imported"
    )


if __name__ == "__main__":
    import_dataset()
