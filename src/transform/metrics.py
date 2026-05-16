import pandas as pd


def _match_result(row: pd.Series, team_id: int) -> str:
    """試合結果を W/D/L で返す"""
    home_id = row["homeTeam_id"]
    away_id = row["awayTeam_id"]
    hg = row["score_fullTime_home"]
    ag = row["score_fullTime_away"]
    if pd.isna(hg) or pd.isna(ag):
        return ""
    if home_id == team_id:
        if hg > ag:
            return "W"
        elif hg == ag:
            return "D"
        else:
            return "L"
    else:
        if ag > hg:
            return "W"
        elif ag == hg:
            return "D"
        else:
            return "L"


def _result_to_points(result: str) -> int:
    return {"W": 3, "D": 1, "L": 0}.get(result, 0)


def build_matches_df(matches_data: dict, team_id: int) -> pd.DataFrame:
    """matches API レスポンスをジュビロ視点のフラット DataFrame に変換"""
    rows = []
    for m in matches_data.get("matches", []):
        status = m.get("status", "")
        if status not in ("FINISHED", "IN_PLAY"):
            continue
        home = m["homeTeam"]
        away = m["awayTeam"]
        score = m.get("score", {})
        ft = score.get("fullTime", {})
        rows.append(
            {
                "match_id": m["id"],
                "matchday": m.get("matchday"),
                "date": m.get("utcDate", "")[:10],
                "homeTeam_id": home["id"],
                "homeTeam_name": home["name"],
                "awayTeam_id": away["id"],
                "awayTeam_name": away["name"],
                "score_fullTime_home": ft.get("home"),
                "score_fullTime_away": ft.get("away"),
                "status": status,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    # ジュビロ関連試合だけに絞る
    df = df[(df["homeTeam_id"] == team_id) | (df["awayTeam_id"] == team_id)].copy()
    df["result"] = df.apply(_match_result, axis=1, team_id=team_id)
    df["points"] = df["result"].map(_result_to_points)
    df["is_home"] = df["homeTeam_id"] == team_id
    df["goals_for"] = df.apply(
        lambda r: r["score_fullTime_home"] if r["is_home"] else r["score_fullTime_away"],
        axis=1,
    )
    df["goals_against"] = df.apply(
        lambda r: r["score_fullTime_away"] if r["is_home"] else r["score_fullTime_home"],
        axis=1,
    )
    df["opponent_name"] = df.apply(
        lambda r: r["awayTeam_name"] if r["is_home"] else r["homeTeam_name"],
        axis=1,
    )
    df["opponent_id"] = df.apply(
        lambda r: r["awayTeam_id"] if r["is_home"] else r["homeTeam_id"],
        axis=1,
    )
    return df.sort_values("date").reset_index(drop=True)


def compute_form(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """直近 n 試合の累積勝点推移"""
    recent = df.tail(n).copy()
    recent["cumulative_points"] = recent["points"].cumsum()
    return recent[["date", "matchday", "opponent_name", "result", "points", "cumulative_points"]]


def compute_home_away(df: pd.DataFrame) -> pd.DataFrame:
    """ホーム/アウェイ別 W/D/L 集計"""
    records = []
    for is_home, label in [(True, "ホーム"), (False, "アウェイ")]:
        sub = df[df["is_home"] == is_home]
        records.append(
            {
                "venue": label,
                "W": (sub["result"] == "W").sum(),
                "D": (sub["result"] == "D").sum(),
                "L": (sub["result"] == "L").sum(),
                "goals_for": sub["goals_for"].sum(),
                "goals_against": sub["goals_against"].sum(),
                "points": sub["points"].sum(),
            }
        )
    return pd.DataFrame(records)


def compute_opponent_record(df: pd.DataFrame) -> pd.DataFrame:
    """対戦相手別 勝率・得失点差"""
    rows = []
    for opp_id, grp in df.groupby("opponent_id"):
        played = len(grp)
        wins = (grp["result"] == "W").sum()
        draws = (grp["result"] == "D").sum()
        losses = (grp["result"] == "L").sum()
        gf = grp["goals_for"].sum()
        ga = grp["goals_against"].sum()
        rows.append(
            {
                "opponent_name": grp["opponent_name"].iloc[0],
                "played": played,
                "W": wins,
                "D": draws,
                "L": losses,
                "win_rate": round(wins / played, 2) if played else 0,
                "goal_diff": int(gf - ga),
            }
        )
    return pd.DataFrame(rows).sort_values("opponent_name").reset_index(drop=True)


def compute_matchday_goals(df: pd.DataFrame) -> pd.DataFrame:
    """節ごとの得点/失点"""
    return (
        df.groupby("matchday")
        .agg(goals_for=("goals_for", "sum"), goals_against=("goals_against", "sum"))
        .reset_index()
    )
