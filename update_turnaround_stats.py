from datetime import datetime, timezone

from database import get_db


def update_turnaround_stats():

    conn = get_db()

    teams = conn.execute(
        """
        SELECT DISTINCT team
        FROM team_stats
        """
    ).fetchall()

    processed = 0

    for row in teams:

        team = row[0]

        home_stats = conn.execute(
            """
            SELECT
                SUM(home_2up),
                SUM(home_turnaround)
            FROM match_results
            WHERE home_team = ?
            """,
            (team,)
        ).fetchone()

        away_stats = conn.execute(
            """
            SELECT
                SUM(away_2up),
                SUM(away_turnaround)
            FROM match_results
            WHERE away_team = ?
            """,
            (team,)
        ).fetchone()

        home_2up = home_stats[0] or 0
        home_failed = home_stats[1] or 0

        away_2up = away_stats[0] or 0
        away_failed = away_stats[1] or 0

        total_leads = home_2up + away_2up
        total_failed = home_failed + away_failed

        turnaround_pct = 0

        if total_leads > 0:
            turnaround_pct = round(
                (total_failed / total_leads) * 100,
                2
            )

        home_pct = 0

        if home_2up > 0:
            home_pct = round(
                (home_failed / home_2up) * 100,
                2
            )

        away_pct = 0

        if away_2up > 0:
            away_pct = round(
                (away_failed / away_2up) * 100,
                2
            )

        conn.execute(
            """
            UPDATE team_stats
            SET
                turnaround_pct = ?,
                two_up_leads = ?,
                failed_leads = ?,
                home_turnaround_pct = ?,
                away_turnaround_pct = ?,
                updated_at = ?
            WHERE team = ?
            """,
            (
                turnaround_pct,
                total_leads,
                total_failed,
                home_pct,
                away_pct,
                datetime.now(
                    timezone.utc
                ).isoformat(),
                team
            )
        )

        processed += 1

    conn.commit()
    conn.close()

    print(
        f"{processed} teams updated"
    )


if __name__ == "__main__":
    update_turnaround_stats()
