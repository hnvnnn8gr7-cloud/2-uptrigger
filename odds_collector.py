from datetime import datetime

import requests

from database import get_db

API_KEY = "ed558120078b3d4c23100523e979ce53"

url = (
    f"https://api.the-odds-api.com/v4/"
    f"sports/soccer/odds/"
    f"?apiKey={API_KEY}"
    f"&regions=uk"
    f"&markets=h2h"
)

response = requests.get(url)

matches = response.json()

conn = get_db()

for match in matches:

    for bookmaker in match.get(
        "bookmakers",
        []
    ):

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

            VALUES

            (?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                match["id"],
                match["home_team"],
                0,
                0
            )
        )

conn.commit()
conn.close()
