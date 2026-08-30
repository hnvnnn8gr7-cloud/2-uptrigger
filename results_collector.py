from datetime import datetime, timedelta, timezone
import requests
import sqlite3

API_FOOTBALL_KEY = "aa7c72b2db786ed876c98fdafd5274b4"

DB_NAME = "two_up.db"


def get_db():
    return sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )


HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}


def detect_turnaround(
    home_team,
    away_team,
    events
):

    home_score = 0
    away_score = 0

    home_2up = False
    away_2up = False

    for event in events:

        if event.get("type") != "Goal":
            continue

        scoring_team = event["team"]["name"]

        if scoring_team == home_team:
            home_score += 1
        elif scoring_team == away_team:
            away_score += 1

        if home_score - away_score >= 2:
            home_2up = True

        if away_score - home_score >= 2:
            away_2up = True

    final_home = home_score
    final_away = away_score

    home_turnaround = 0
    away_turnaround = 0

    if home_2up and final_home <= final_away:
        home_turnaround = 1

    if away_2up and final_away <= final_home:
        away_turnaround = 1

    return (
        final_home,
        final_away,
        int(home_2up),
        int(away_2up),
        home_turnaround,
        away_turnaround
    )


def save_result(
    fixture_id,
    league,
    home_team,
    away_team,
    final_home,
    final_away,
    home_2up,
    away_2up,
    home_turnaround,
    away_turnaround
):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO match_results
        (
            match_id,
            league,
            home_team,
            away_team,
            final_home,
            final_away,
            home_2up,
            away_2up,
            home_turnaround,
            away_turnaround,
            processed_at
        )
        VALUES
        (
            ?,?,?,?,?,?,?,?,?,?,?
        )
        """,
        (
            str(fixture_id),
            league,
            home_team,
            away_team,
            final_home,
            final_away,
            home_2up,
            away_2up,
            home_turnaround,
            away_turnaround,
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_yesterdays_fixtures():

    yesterday = (
        datetime.now(timezone.utc)
        - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?date={yesterday}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    return response.json().get(
        "response",
        []
    )


def get_fixture_events(
    fixture_id
):

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures/events?fixture={fixture_id}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    return response.json().get(
        "response",
        []
    )


def process_results():

    fixtures = get_yesterdays_fixtures()

    processed = 0

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

        league = (
            fixture["league"]["name"]
        )

        events = get_fixture_events(
            fixture_id
        )

        (
            final_home,
            final_away,
            home_2up,
            away_2up,
            home_turnaround,
            away_turnaround
        ) = detect_turnaround(
            home_team,
            away_team,
            events
        )

        save_result(
            fixture_id,
            league,
            home_team,
            away_team,
            final_home,
            final_away,
            home_2up,
            away_2up,
            home_turnaround,
            away_turnaround
        )

        processed += 1

    print(
        f"{processed} fixtures processed"
    )


if __name__ == "__main__":

    process_results()
