import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
RAPIDAPI_HOST = "api-football-v1.p.rapidapi.com"
J1_LEAGUE_ID = 98
TEAM_NAME = "Jubilo Iwata"

_RATE_LIMIT_SLEEP = 1


class ApiFootballClient:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("RAPIDAPI_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        })

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
        resp.raise_for_status()
        time.sleep(_RATE_LIMIT_SLEEP)
        return resp.json()

    # ── 正規化済みレスポンス (football-data.org 互換フォーマット) ──────────────

    def get_standings(self, season: int) -> dict:
        raw = self._get("/standings", params={"league": J1_LEAGUE_ID, "season": season})
        return _normalize_standings(raw)

    def get_matches(self, season: int, team_id: int | None = None) -> dict:
        params: dict = {"league": J1_LEAGUE_ID, "season": season}
        if team_id:
            params["team"] = team_id
        raw = self._get("/fixtures", params=params)
        return _normalize_matches(raw)

    def get_scorers(self, season: int, limit: int = 20) -> dict:
        raw = self._get("/players/topscorers", params={"league": J1_LEAGUE_ID, "season": season})
        return _normalize_scorers(raw, limit)

    def find_team_id(self, standings: dict) -> int | None:
        for table in standings.get("standings", []):
            for row in table.get("table", []):
                if TEAM_NAME.lower() in row["team"]["name"].lower():
                    return row["team"]["id"]
        return None


# ── 正規化ヘルパー ────────────────────────────────────────────────────────────

def _normalize_standings(raw: dict) -> dict:
    rows = []
    for entry in raw.get("response", []):
        league = entry.get("league", {})
        for group in league.get("standings", []):
            for r in group:
                team = r.get("team", {})
                all_stats = r.get("all", {})
                goals = all_stats.get("goals", {})
                rows.append({
                    "position": r.get("rank"),
                    "team": {"id": team.get("id"), "name": team.get("name", "")},
                    "playedGames": all_stats.get("played", 0),
                    "won": all_stats.get("win", 0),
                    "draw": all_stats.get("draw", 0),
                    "lost": all_stats.get("lose", 0),
                    "goalsFor": goals.get("for", 0),
                    "goalsAgainst": goals.get("against", 0),
                    "goalDifference": r.get("goalsDiff", 0),
                    "points": r.get("points", 0),
                })
    return {"standings": [{"type": "TOTAL", "table": rows}]}


def _extract_matchday(round_str: str | None) -> int | None:
    m = re.search(r"\d+", round_str or "")
    return int(m.group()) if m else None


def _normalize_matches(raw: dict) -> dict:
    matches = []
    for f in raw.get("response", []):
        fixture = f.get("fixture", {})
        status_short = fixture.get("status", {}).get("short", "")
        status_map = {"FT": "FINISHED", "1H": "IN_PLAY", "2H": "IN_PLAY", "HT": "IN_PLAY"}
        status = status_map.get(status_short, status_short)

        teams = f.get("teams", {})
        goals = f.get("goals", {})
        league = f.get("league", {})

        matches.append({
            "id": fixture.get("id"),
            "matchday": _extract_matchday(league.get("round")),
            "utcDate": (fixture.get("date") or "")[:10],
            "status": status,
            "homeTeam": {
                "id": teams.get("home", {}).get("id"),
                "name": teams.get("home", {}).get("name", ""),
            },
            "awayTeam": {
                "id": teams.get("away", {}).get("id"),
                "name": teams.get("away", {}).get("name", ""),
            },
            "score": {
                "fullTime": {
                    "home": goals.get("home"),
                    "away": goals.get("away"),
                }
            },
        })
    return {"matches": matches}


def _normalize_scorers(raw: dict, limit: int) -> dict:
    scorers = []
    for entry in raw.get("response", [])[:limit]:
        player = entry.get("player", {})
        stats = (entry.get("statistics") or [{}])[0]
        goals_info = stats.get("goals", {})
        games_info = stats.get("games", {})
        team_info = stats.get("team", {})
        scorers.append({
            "player": {"name": player.get("name", "")},
            "team": {"name": team_info.get("name", "")},
            "goals": goals_info.get("total") or 0,
            "assists": goals_info.get("assists") or 0,
            "playedMatches": games_info.get("appearences") or 0,
        })
    return {"scorers": scorers}
