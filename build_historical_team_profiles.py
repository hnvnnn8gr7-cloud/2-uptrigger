import pandas as pd
from datetime import datetime, timezone

from database import get_db


CSV_FILE = "2up_multi_league_dataset.csv"


def build_profiles():

    df = pd.read_csv(CSV_FILE)

    conn = get_db()

    teams = df["trigger_team"].unique()

    updated = 0

    for team in teams:

        team_df = df[
            df["trigger_team"] == team
        ]

        matches = len(team_df)

        two_up = len(
            team_df[
                team_df["2up_triggered"] == True
            ]
        )

        comebacks = len(
            team_df[
                team_df["comeback_occurred"] == True
            ]
        )

        trigger_rate = 0

        if matches > 0:
            trigger_rate = round(
                (two_up / matches) * 100,
                2
            )

        turnaround_rate = 0

        if two_up > 0:
            turnaround_rate = round(
                (comebacks / two_up) * 100,
                2
            )

        conn.execute(
            """
            INSERT OR IGNORE INTO team_stats
            (
                team
            )
            VALUES
            (?)
            """,
            (team,)
        )

        conn.execute(
            """
            UPDATE team_stats
            SET
                historical_matches = ?,
                historical_two_up = ?,
                two_up_trigger_rate = ?,
                historical_comebacks = ?,
                historical_turnaround_rate = ?,
                updated_at = ?
            WHERE team = ?
            """,
            (
                matches,
                two_up,
                trigger_rate,
                comebacks,
                turnaround_rate,
                datetime.now(
                    timezone.utc
                ).isoformat(),
                team
            )
        )

        updated += 1

    conn.commit()
    conn.close()

    print(
        f"{updated} team profiles created"
    )


if __name__ == "__main__":
    build_profiles()
