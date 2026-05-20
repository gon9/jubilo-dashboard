"""
日次データ取得スクリプト。
GitHub Actions または手動で実行する。

Usage:
    python scripts/fetch_all.py [--season 2025]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.fetch.api_football import ApiFootballClient


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved: {path}")


def main(season: int) -> None:
    client = ApiFootballClient()
    data_dir = ROOT / "data"

    print(f"Fetching season {season} ...")

    standings, league_id = client.get_standings(season)
    save_json(data_dir / "standings.json", standings)

    team_id = client.find_team_id(standings)
    if team_id is None:
        print("WARNING: Jubilo Iwata not found in standings. Check team name or season.")
    else:
        print(f"Jubilo Iwata team_id={team_id} league_id={league_id}")
    save_json(data_dir / "meta.json", {"team_id": team_id, "season": season, "league_id": league_id})

    matches = client.get_matches(season, team_id=team_id, league_id=league_id)
    save_json(data_dir / "matches.json", matches)

    scorers = client.get_scorers(season, league_id=league_id)
    save_json(data_dir / "scorers.json", scorers)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2025)
    args = parser.parse_args()
    main(args.season)
