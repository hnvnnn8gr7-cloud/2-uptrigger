import requests
import time

from datetime import (
    datetime,
    timedelta,
    timezone
)

from database import get_db

from team_normalizer import (
    normalize_team
)

from bookmakers import (
    get_enabled_bookmakers
)

# ==================================
# CONFIG
# ==================================

API_KEY = "cb23a6f3-5d30-47f1-8f0c-33137e430799"

BASE_URL = "https://api.oddspapi.io/v4"

SPORT_ID = 10

LOOKAHEAD_DAYS = 7

# ==================================
# DATABASE
# ==================================


def save_odds_row(
    match_id,
    kickoff,
    league,
    home_team,
    away_team,
    selection,
    bookmaker,
    back_odds
):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO odds_history
        (
            timestamp,

            match_id,

            kickoff,
            league,

            home_team,
            away_team,

            selection,

            bookmaker,

            exchange_name,

            back_odds,

            lay_odds
        )

        VALUES
        (
            ?,?,?,?,?,?,
            ?,?,?,?,
            ?
        )
        """,
        (
            datetime.now(
                timezone.utc
            ).isoformat(),

            match_id,

            kickoff,
            league,

            home_team,
            away_team,

            selection,

            bookmaker,

            None,

            back_odds,

            None
        )
    )

    conn.commit()
    conn.close()


def clear_existing_odds():

    conn = get_db()

    conn.execute(
        """
        DELETE FROM odds_history
        """
    )

    conn.commit()
    conn.close()


# ==================================
# API HELPERS
# ==================================


def get_fixtures():

    today = datetime.utcnow()

    future = (
        today +
        timedelta(
            days=LOOKAHEAD_DAYS
        )
    )

    response = requests.get(
        f"{BASE_URL}/fixtures",
        params={
            "sportId": SPORT_ID,
            "from": today.strftime(
                "%Y-%m-%d"
            ),
            "to": future.strftime(
                "%Y-%m-%d"
            ),
            "statusId": 0,
            "hasOdds": "true",
            "apiKey": API_KEY
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def get_fixture_odds(
    fixture_id,
    bookmaker
):

    response = requests.get(
        f"{BASE_URL}/odds",
        params={
            "fixtureId": fixture_id,
            "bookmakers": bookmaker,
            "oddsFormat": "decimal",
            "language": "en",
            "verbosity": 3,
            "apiKey": API_KEY
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ==================================
# ODDS PARSER
# ==================================


def extract_match_odds(
    odds_response,
    bookmaker_key
):

    bookmaker_data = (
        odds_response
        .get(
            "bookmakerOdds",
            {}
        )
        .get(
            bookmaker_key,
            {}
        )
    )

    if not bookmaker_data:
        return []

    markets = bookmaker_data.get(
        "markets",
        {}
    )

    opportunities = []

    for market_id, market in markets.items():

        outcomes = market.get(
            "outcomes",
            {}
        )

        for outcome_id, outcome in outcomes.items():

            players = outcome.get(
                "players",
                {}
            )

            if not players:
                continue

            first_player = list(
                players.values()
            )[0]

            odds = first_player.get(
                "price"
            )

            outcome_code = (
                first_player.get(
                    "bookmakerOutcomeId"
                )
            )

            opportunities.append(
                {
                    "outcome_code":
                        outcome_code,

                    "odds":
                        odds
                }
            )

    return opportunities


# ==================================
# MAIN COLLECTOR
# ==================================


def collect_odds():

    print(
        "Collecting OddsPapi fixtures..."
    )

    clear_existing_odds()

    fixtures = get_fixtures()

    enabled_bookmakers = (
        get_enabled_bookmakers()
    )

    saved_rows = 0

    for fixture in fixtures:

        fixture_id = fixture[
            "fixtureId"
        ]

        kickoff = fixture[
            "startTime"
        ]

        league = fixture[
            "tournamentName"
        ]

        home_team = normalize_team(
            fixture[
                "participant1Name"
            ]
        )

        away_team = normalize_team(
            fixture[
                "participant2Name"
            ]
        )

        for bookmaker in enabled_bookmakers:

            try:

                odds_data = (
                    get_fixture_odds(
                        fixture_id,
                        bookmaker
                    )
                )

                selections = (
                    extract_match_odds(
                        odds_data,
                        bookmaker
                    )
                )

                for selection in selections:

                    outcome_code = (
                        str(
                            selection[
                                "outcome_code"
                            ]
                        ).lower()
                    )

                    if (
                        outcome_code
                        == "home"
                    ):
                        team = (
                            home_team
                        )

                    elif (
                        outcome_code
                        == "away"
                    ):
                        team = (
                            away_team
                        )

                    else:
                        continue

                    save_odds_row(
                        match_id=
                        fixture_id,

                        kickoff=
                        kickoff,

                        league=
                        league,

                        home_team=
                        home_team,

                        away_team=
                        away_team,

                        selection=
                        team,

                        bookmaker=
                        bookmaker,

                        back_odds=
                        float(
                            selection[
                                "odds"
                            ]
                        )
                    )

                    saved_rows += 1

                time.sleep(
                    0.5
                )

            except Exception as exc:

                print(
                    f"Failed "
                    f"{fixture_id} "
                    f"{bookmaker}: "
                    f"{exc}"
                )

    print(
        f"Saved "
        f"{saved_rows} "
        f"odds rows"
    )


# ==================================
# RUN
# ==================================

if __name__ == "__main__":

    collect_odds()
