from datetime import datetime, timezone
import requests

from database import get_db

API_KEY = "YOUR_API_KEY"


def collect_odds():

    url = (
        f"https://api.the-odds-api.com/v4/"
        f"sports/soccer/odds/"
        f"?apiKey={API_KEY}"
        f"&regions=uk,eu"
        f"&markets=h2h"
        f"&oddsFormat=decimal"
    )

    response = requests.get(url, timeout=20)

    if response.status_code != 200:
        print("Failed to fetch odds")
        return

    matches = response.json()

    conn = get_db()

    rows_added = 0

    for match in matches:

        match_id = match.get("id")

        for bookmaker in match.get(
            "bookmakers",
            []
        ):

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

                    odds = outcome.get(
                        "price"
                    )

                    team = outcome.get(
                        "name"
                    )

                    conn.execute(
                        """
                        INSERT INTO odds_history
                        (
                            timestamp,
                            match_id,
                            team,
                            back_odds,
                            lay_odds
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            datetime.now(
                                timezone.utc
                            ).isoformat(),
                            match_id,
                            team,
                            float(odds),
                            None
                        )
                    )

                    rows_added += 1

    conn.commit()
    conn.close()

    print(
        f"{rows_added} odds stored"
    )


if __name__ == "__main__":
    collect_odds()
