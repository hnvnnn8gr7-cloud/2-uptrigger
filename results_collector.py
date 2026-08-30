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


def create_processed_fixtures_table():

    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS processed_fixtures (
        fixture_id TEXT PRIMARY KEY,
        processed_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def fixture_already_processed(
    fixture_id
):

    conn = get_db()

    row = conn.execute(
        """
        SELECT fixture_id
        FROM processed_fixtures
        WHERE fixture_id = ?
        """,
        (str(fixture_id),)
    ).fetchone()

    conn.close()

    return row is not None


def mark_fixture_processed(
    fixture_id
):

    conn = get_db()

    conn.execute(
        """
        INSERT OR REPLACE INTO
        processed_fixtures
        (
            fixture_id,
            processed_at
        )
        VALUES (?, ?)
        """,
        (
            str(fixture_id),
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    )

    conn.commit()
    conn.close()


def get_completed_fixtures():

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

    return fixtures


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

    data = response.json()

    return data.get(
        "response",
        []
    )


def detect_2up_turnaround(
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

        scoring_team = (
            event["team"]["name"]
        )

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

    home_turnaround = int(
        home_2up and final_home <= final_away
    )

    away_turnaround = int(
        away_2up and final_away <= final_home
    )

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


def process_results():

    create_processed_fixtures_table()

    fixtures = get_completed_fixtures()

    processed = 0
    skipped = 0

    for fixture in fixtures:

        fixture_id = (
            fixture["fixture"]["id"]
        )

        if fixture_already_processed(
            fixture_id
        ):
            skipped += 1
            continue

        league = (
            fixture["league"]["name"]
        )

        home_team = (
            fixture["teams"]["home"]["name"]
        )

        away_team = (
            fixture["teams"]["away"]["name"]
        )

        print(
            f"Processing fixture {fixture_id}"
        )

        events = get_fixture_events(
            fixture_id
        )

        result = detect_2up_turnaround(
            home_team,
            away_team,
            events
        )

        save_result(
            fixture_id,
            league,
            home_team,
            away_team,
            *result
        )

        mark_fixture_processed(
            fixture_id
        )

        processed += 1

    print(
        f"{processed} new fixtures processed"
    )

    print(
        f"{skipped} fixtures skipped"
    )


if __name__ == "__main__":
    process_results()
