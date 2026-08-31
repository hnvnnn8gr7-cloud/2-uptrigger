from datetime import datetime, timezone

from database import get_db


def build_training_data():

    conn = get_db()

    conn.execute(
        "DELETE FROM training_data"
    )

    matches = conn.execute(
        """
        SELECT
            match_id,
            league,

            home_team,
            away_team,

            home_turnaround,
            away_turnaround,

            home_lead_minute,
            away_lead_minute

        FROM match_results
        """
    ).fetchall()

    inserted = 0

    for match in matches:

        (
            match_id,
            league,

            home_team,
            away_team,

            home_turnaround,
            away_turnaround,

            home_lead_minute,
            away_lead_minute

        ) = match

        home_stats = conn.execute(
            """
            SELECT

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                two_up_trigger_rate,

                historical_turnaround_rate

            FROM team_stats

            WHERE team = ?
            """,
            (home_team,)
        ).fetchone()

        away_stats = conn.execute(
            """
            SELECT

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                two_up_trigger_rate,

                historical_turnaround_rate

            FROM team_stats

            WHERE team = ?
            """,
            (away_team,)
        ).fetchone()

        if not home_stats:
            continue

        if not away_stats:
            continue

        conn.execute(
            """
            INSERT INTO training_data
            (
                match_id,
                league,

                team,

                is_home,

                back_odds,
                lay_odds,

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                two_up_trigger_rate,

                historical_turnaround_rate,

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
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?
            )
            """,
            (
                match_id,
                league,

                home_team,

                1,

                0,
                0,

                home_stats[0],
                home_stats[1],

                home_stats[2],
                home_stats[3],

                home_stats[4],

                home_stats[5],

                home_stats[6],

                home_lead_minute or 0,

                2,

                0,
                0,

                0,
                0,

                0,
                0,

                1.0,

                home_turnaround,

                datetime.now(
                    timezone.utc
                ).isoformat()
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

                back_odds,
                lay_odds,

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                two_up_trigger_rate,

                historical_turnaround_rate,

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
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?
            )
            """,
            (
                match_id,
                league,

                away_team,

                0,

                0,
                0,

                away_stats[0],
                away_stats[1],

                away_stats[2],
                away_stats[3],

                away_stats[4],

                away_stats[5],

                away_stats[6],

                away_lead_minute or 0,

                2,

                0,
                0,

                0,
                0,

                0,
                0,

                1.0,

                away_turnaround,

                datetime.now(
                    timezone.utc
                ).isoformat()
            )
        )

        inserted += 2

    conn.commit()

    conn.close()

    print(
        f"{inserted} API training rows built"
    )


if __name__ == "__main__":
    build_training_data()
