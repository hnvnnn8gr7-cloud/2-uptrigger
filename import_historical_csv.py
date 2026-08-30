import pandas as pd
from datetime import datetime, timezone

from database import get_db


CSV_FILE = "historical_results.csv"


def get_weight(season):

    season = str(season)

    if "2025" in season:
        return 1.0

    if "2024" in season:
        return 0.9

    if "2023" in season:
        return 0.8

    if "2022" in season:
        return 0.7

    if "2021" in season:
        return 0.6

    return 0.5


def import_csv():

    df = pd.read_csv(
        CSV_FILE
    )

    conn = get_db()

    inserted = 0

    for _, row in df.iterrows():

        home_ht = int(row["HTHG"])
        away_ht = int(row["HTAG"])

        home_ft = int(row["FTHG"])
        away_ft = int(row["FTAG"])

        full_turnaround = 0

        if (
            home_ht - away_ht >= 2
            and
            home_ft <= away_ft
        ):
            full_turnaround = 1

        if (
            away_ht - home_ht >= 2
            and
            away_ft <= home_ft
        ):
            full_turnaround = 1

        weight = get_weight(
            row.get(
                "Season",
                "2020"
            )
        )

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

                full_turnaround,

                sample_weight,

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

                row.get(
                    "Div",
                    "Unknown"
                ),

                row.get(
                    "HomeTeam",
                    "Unknown"
                ),

                1,

                0,
                0,

                0,
                0,

                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                full_turnaround,

                weight,

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
    import_csv()
