import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.football-data.org/v4"
# J1 League の competition code
COMPETITION_CODE = "JL"
# ジュビロ磐田のチーム名 (standings から動的に解決する)
TEAM_NAME = "Jubilo Iwata"

_RATE_LIMIT_SLEEP = 6  # 無料枠: 10 req/min → 6秒インターバル


class FootballDataClient:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("FOOTBALL_DATA_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": key})

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        time.sleep(_RATE_LIMIT_SLEEP)
        return resp.json()

    def get_competition(self) -> dict:
        return self._get(f"/competitions/{COMPETITION_CODE}")

    def get_standings(self, season: int) -> dict:
        return self._get(
            f"/competitions/{COMPETITION_CODE}/standings",
            params={"season": season},
        )

    def get_matches(self, season: int) -> dict:
        return self._get(
            f"/competitions/{COMPETITION_CODE}/matches",
            params={"season": season},
        )

    def get_scorers(self, season: int, limit: int = 20) -> dict:
        return self._get(
            f"/competitions/{COMPETITION_CODE}/scorers",
            params={"season": season, "limit": limit},
        )

    def find_team_id(self, standings: dict) -> int | None:
        for table in standings.get("standings", []):
            for row in table.get("table", []):
                if TEAM_NAME.lower() in row["team"]["name"].lower():
                    return row["team"]["id"]
        return None
