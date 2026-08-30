import requests
import json

API_FOOTBALL_KEY = "YOUR_API_KEY"

headers = {
    "x-apisports-key": API_FOOTBALL_KEY
}

fixture_id = 123456

url = (
    "https://v3.football.api-sports.io/"
    f"fixtures/statistics?fixture={fixture_id}"
)

response = requests.get(
    url,
    headers=headers,
    timeout=20
)

print("Status:", response.status_code)

print(
    json.dumps(
        response.json(),
        indent=2
    )
)
