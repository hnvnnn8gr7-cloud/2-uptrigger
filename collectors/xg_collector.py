from datetime import (
    datetime,
    timedelta,
    timezone
)

import sqlite3
import requests


API_FOOTBALL_KEY = (
    "aa7c72b2db786ed876c98fdafd5274b4"
)

DB_NAME = "two_up.db"

HEADERS = {
    "x-apisports-key":
        API_FOOTBALL_KEY
}


def get_db():

    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


def save_team_stats(
    team,
    avg_xg,
    avg_xga,
    goals_last5,
    conceded_last5,
    matches_played
):

    xg_edge = (
        avg_xg -
        avg_xga
    )

    conn = get_db()

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

            avg_xg = ?,
            avg_xga = ?,

            xg_edge = ?,

            goals_last5 = ?,
            conceded_last5 = ?,

            matches_played = ?,

            updated_at = ?

        WHERE team = ?
        """,
        (
            avg_xg,
            avg_xga,

            xg_edge,

            goals_last5,
            conceded_last5,

            matches_played,

            datetime.now(
                timezone.utc
            ).isoformat(),

            team
        )
    )

    conn.commit()
    conn.close()


def get_recent_fixtures():

    date_from = (
        datetime.utcnow()
        - timedelta(days=60)
    ).strftime(
        "%Y-%m-%d"
    )

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?from={date_from}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    data = response.json()

    return data.get(
        "response",
        []
    )


def get_fixture_statistics(
    fixture_id
):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures/statistics?fixture={fixture_id}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    data = response.json()

    return data.get(
        "response",
        []
    )


def extract_stat(
    stats,
    stat_name
):

    for item in stats:

        if (
            item["type"]
            == stat_name
        ):
            return item["value"]

    return 0


def process_xg():

    fixtures = (
        get_recent_fixtures()
    )

    team_data = {}

    for fixture in fixtures:

        fixture_id = (
            fixture["fixture"]["id"]
        )

        stats = (
            get_fixture_statistics(
                fixture_id
            )
        )

        if len(stats) < 2:
            continue

        home_team = (
            stats[0]["team"]["name"]
        )

        away_team = (
            stats[1]["team"]["name"]
        )

        home_stats = (
            stats[0]["statistics"]
        )

        away_stats = (
            stats[1]["statistics"]
        )

        home_goals = (
            fixture["goals"]["home"]
            or 0
        )

        away_goals = (
            fixture["goals"]["away"]
            or 0
        )

        home_xg = extract_stat(
            home_stats,
            "Expected Goals"
        )

        away_xg = extract_stat(
            away_stats,
            "Expected Goals"
        )

        try:
            home_xg = float(
                home_xg
            )
        except:
            home_xg = (
                home_goals
            )

        try:
            away_xg = float(
                away_xg
            )
        except:
            away_xg = (
                away_goals
            )

        for team in [
            home_team,
            away_team
        ]:

            if team not in team_data:

                team_data[
                    team
                ] = {
                    "xg": [],
                    "xga": [],
                    "goals": [],
                    "conceded": []
                }

        team_data[
            home_team
        ]["xg"].append(
            home_xg
        )

        team_data[
            home_team
        ]["xga"].append(
            away_xg
        )

        team_data[
            home_team
        ]["goals"].append(
            home_goals
        )

        team_data[
            home_team
        ]["conceded"].append(
            away_goals
        )

        team_data[
            away_team
        ]["xg"].append(
            away_xg
        )

        team_data[
            away_team
        ]["xga"].append(
            home_xg
        )

        team_data[
            away_team
        ]["goals"].append(
            away_goals
        )

        team_data[
            away_team
        ]["conceded"].append(
            home_goals
        )

    for team, values in team_data.items():

        matches_played = len(
            values["xg"]
        )

        if matches_played == 0:
            continue

        avg_xg = round(
            sum(values["xg"])
            /
            matches_played,
            2
        )

        avg_xga = round(
            sum(values["xga"])
            /
            matches_played,
            2
        )

        goals_last5 = round(
            sum(
                values["goals"][-5:]
            ),
            2
        )

        conceded_last5 = round(
            sum(
                values["conceded"][-5:]
            ),
            2
        )

        save_team_stats(
            team,
            avg_xg,
            avg_xga,
            goals_last5,
            conceded_last5,
            matches_played
        )

    print(
        f"Updated {len(team_data)} teams"
    )


if __name__ == "__main__":

    process_xg()
