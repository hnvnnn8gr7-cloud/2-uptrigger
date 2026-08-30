from datetime import datetime, timedelta, timezone
import sqlite3
import requests

API_FOOTBALL_KEY = "aa7c72b2db786ed876c98fdafd5274b4"

DB_NAME = "two_up.db"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
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

    conn = get_db()

    conn.execute(
        """
        INSERT OR REPLACE INTO team_stats
        (
            team,
            avg_xg,
            avg_xga,
            goals_last5,
            conceded_last5,
            matches_played,
            updated_at
        )
        VALUES
        (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            team,
            avg_xg,
            avg_xga,
            goals_last5,
            conceded_last5,
            matches_played,
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_recent_fixtures():

    yesterday = (
        datetime.now(
            timezone.utc
        )
        - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?date={yesterday}&status=FT"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
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
        timeout=20
    )

    data = response.json()

    return data.get(
        "response",
        []
    )


def process_xg():

    fixtures = get_recent_fixtures()

    team_data = {}

    for fixture in fixtures:

        fixture_id = (
            fixture["fixture"]["id"]
        )

        home_team = (
            fixture["teams"]["home"]["name"]
        )

        away_team = (
            fixture["teams"]["away"]["name"]
        )

        home_goals = (
            fixture["goals"]["home"] or 0
        )

        away_goals = (
            fixture["goals"]["away"] or 0
        )

        stats = get_fixture_statistics(
            fixture_id
        )

        home_xg = 0
        away_xg = 0

        for team_stats in stats:

            team_name = (
                team_stats["team"]["name"]
            )

            for stat in team_stats["statistics"]:

                if (
                    stat["type"]
                    == "Expected Goals"
                ):

                    try:

                        value = float(
                            stat["value"]
                        )

                    except:

                        value = 0

                    if team_name == home_team:
                        home_xg = value

                    if team_name == away_team:
                        away_xg = value

        if home_team not in team_data:

            team_data[home_team] = {
                "xg": [],
                "xga": [],
                "gf": [],
                "ga": []
            }

        if away_team not in team_data:

            team_data[away_team] = {
                "xg": [],
                "xga": [],
                "gf": [],
                "ga": []
            }

        team_data[home_team]["xg"].append(
            home_xg
        )

        team_data[home_team]["xga"].append(
            away_xg
        )

        team_data[home_team]["gf"].append(
            home_goals
        )

        team_data[home_team]["ga"].append(
            away_goals
        )

        team_data[away_team]["xg"].append(
            away_xg
        )

        team_data[away_team]["xga"].append(
            home_xg
        )

        team_data[away_team]["gf"].append(
            away_goals
        )

        team_data[away_team]["ga"].append(
            home_goals
        )

    for team, stats in team_data.items():

        matches = len(
            stats["xg"]
        )

        if matches == 0:
            continue

        avg_xg = (
            sum(stats["xg"])
            / matches
        )

        avg_xga = (
            sum(stats["xga"])
            / matches
        )

        goals_last5 = sum(
            stats["gf"][-5:]
        )

        conceded_last5 = sum(
            stats["ga"][-5:]
        )

        save_team_stats(
            team,
            round(avg_xg, 2),
            round(avg_xga, 2),
            goals_last5,
            conceded_last5,
            matches
        )

        print(
            f"{team} "
            f"xG={avg_xg:.2f} "
            f"xGA={avg_xga:.2f}"
        )


if __name__ == "__main__":

    process_xg()
