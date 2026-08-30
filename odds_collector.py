from datetime import datetime, timezone
import requests

from database import get_db

# Replace with your actual Odds API key
API_KEY = "ed558120078b3d4c23100523e979ce53"


def collect_odds():

    url = (
        f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
        f"?apiKey={API_KEY}"
        f"&regions=uk,eu"
        f"&markets=h2h"
        f"&oddsFormat=decimal"
    )

    response = requests.get(
        url,
        timeout=20
    )

    if response.status_code != 200:
        print(
            f"Error fetching odds: {response.status_code}"
        )
        return

    matches = response.json()

    conn = get_db()

    rows_added = 0

    for match in matches:

        match_id = match.get("id")

        kickoff = match.get(
            "commence_time"
        )

        league = match.get(
            "sport_title",
            "Unknown"
        )

        home_team = match.get(
            "home_team",
            ""
        )

        away_team = match.get(
            "away_team",
            ""
        )

        for bookmaker in match.get(
            "bookmakers",
            []
        ):

            bookmaker_name = bookmaker.get(
                "title",
                "Unknown"
            )

            for market in bookmaker.get(
                "markets",
                []
            ):

                if market.get("key") != "h2h":
                    continue

                for outcome in market.get(
                    "outcomes",
                    []
                ):

                    selection = outcome.get(
                        "name"
                    )

                    back_odds = float(
                        outcome.get(
                            "price"
                        )
                    )

                    # Estimated lay price
                    lay_odds = round(
                        back_odds * 1.02,
                        2
                    )

                    conn.execute(
                        """
                        INSERT INTO odds_history (
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
                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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

                            bookmaker_name,

                            "Estimated Exchange",

                            back_odds,

                            lay_odds
                        )
                    )

                    rows_added += 1

    conn.commit()

    conn.close()

    print(
        f"{rows_added} rows stored"
    )


if __name__ == "__main__":
    collect_odds()
