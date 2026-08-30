from datetime import datetime, timedelta, timezone
import requests
import sqlite3

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


def get_completed_fixtures():

    yesterday = "2026-08-29"

    url = (
        "https://v3.football.api-sports.io/"
        f"fixtures?date={yesterday}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )

    print(
        f"Fixture request status: {response.status_code}"
    )

    data = response.json()

    fixtures = data.get(
        "response",
        []
    )

    print(
        f"Fixtures found: {len(fixtures)}"
    )

    return fixtures[:100]


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
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def process_results():

    fixtures = get_completed_fixtures()

    processed = 0

    for fixture in fixtures:

        fixture_id = fixture["fixture"]["id"]

        league = fixture["league"]["name"]

        home_team = (
            fixture["teams"]["home"]["name"]
        )

        away_team = (
            fixture["teams"]["away"]["name"]
        )

        final_home = (
            fixture["goals"]["home"]
            if fixture["goals"]["home"] is not None
            else 0
        )

        final_away = (
            fixture["goals"]["away"]
            if fixture["goals"]["away"] is not None
            else 0
        )

        print(
            f"Processing {processed + 1}/{len(fixtures)}"
        )

        save_result(
            fixture_id,
            league,
            home_team,
            away_team,
            final_home,
            final_away,
            0,
            0,
            0,
            0
        )

        processed += 1

    print(
        f"{processed} fixtures processed"
    )


if __name__ == "__main__":
    process_results()
