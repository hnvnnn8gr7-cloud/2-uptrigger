import pandas as pd

from datetime import (
    datetime,
    timezone
)

from database import (
    get_db,
    save_league_stats
)

CSV_FILE = (
    "2up_multi_league_dataset.csv"
)


def build_profiles():

    df = pd.read_csv(
        CSV_FILE
    )

    conn = get_db()

    build_league_statistics(
        df
    )

    teams = df[
        "trigger_team"
    ].dropna().unique()

    updated = 0

    for team in teams:

        team_df = df[
            df[
                "trigger_team"
            ] == team
        ]

        matches = len(
            team_df
        )

        two_up = len(
            team_df[
                team_df[
                    "2up_triggered"
                ] == True
            ]
        )

        comebacks = len(
            team_df[
                team_df[
                    "comeback_occurred"
                ] == True
            ]
        )

        trigger_rate = 0

        if matches > 0:

            trigger_rate = round(
                (
                    two_up
                    /
                    matches
                )
                * 100,
                2
            )

        turnaround_rate = 0

        if two_up > 0:

            turnaround_rate = round(
                (
                    comebacks
                    /
                    two_up
                )
                * 100,
                2
            )

        league_rates = []

        if "league" in team_df.columns:

            for league in (
                team_df["league"]
                .dropna()
                .unique()
            ):

                league_df = df[
                    df["league"]
                    == league
                ]

                league_two_up = len(
                    league_df[
                        league_df[
                            "2up_triggered"
                        ] == True
                    ]
                )

                league_comebacks = len(
                    league_df[
                        league_df[
                            "comeback_occurred"
                        ] == True
                    ]
                )

                if league_two_up > 0:

                    league_rates.append(
                        (
                            league_comebacks
                            /
                            league_two_up
                        )
                        * 100
                    )

        league_turnaround_rate = 0

        if league_rates:

            league_turnaround_rate = round(
                sum(
                    league_rates
                )
                /
                len(
                    league_rates
                ),
                2
            )

        conn.execute(
            """
            INSERT OR IGNORE INTO
            team_stats
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

                historical_comebacks = ?,

                two_up_trigger_rate = ?,

                historical_turnaround_rate = ?,

                league_turnaround_rate = ?,

                updated_at = ?

            WHERE team = ?
            """,
            (
                matches,

                two_up,

                comebacks,

                trigger_rate,

                turnaround_rate,

                league_turnaround_rate,

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
        f"{updated} historical team profiles built"
    )


def build_league_statistics(
    df
):

    if "league" not in df.columns:
        return

    leagues = (
        df["league"]
        .dropna()
        .unique()
    )

    for league in leagues:

        league_df = df[
            df["league"] == league
        ]

        matches = len(
            league_df
        )

        two_up = len(
            league_df[
                league_df[
                    "2up_triggered"
                ] == True
            ]
        )

        comebacks = len(
            league_df[
                league_df[
                    "comeback_occurred"
                ] == True
            ]
        )

        trigger_rate = 0

        if matches > 0:

            trigger_rate = round(
                (
                    two_up
                    /
                    matches
                )
                * 100,
                2
            )

        turnaround_rate = 0

        if two_up > 0:

            turnaround_rate = round(
                (
                    comebacks
                    /
                    two_up
                )
                * 100,
                2
            )

        save_league_stats(
            league=league,
            matches=matches,
            two_up_count=two_up,
            comeback_count=comebacks,
            trigger_rate=trigger_rate,
            turnaround_rate=turnaround_rate
        )

    print(
        "League statistics updated"
    )


if __name__ == "__main__":

    build_profiles()
