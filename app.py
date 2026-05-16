import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.transform.metrics import (
    build_matches_df,
    compute_form,
    compute_home_away,
    compute_matchday_goals,
    compute_opponent_record,
)

DATA_DIR = Path(__file__).parent / "data"

st.set_page_config(
    page_title="ジュビロ磐田 ダッシュボード",
    page_icon="⚽",
    layout="wide",
)


# ── データロード ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_team_id() -> int | None:
    meta = load_json("meta.json")
    return meta.get("team_id")


def get_matches_df() -> pd.DataFrame:
    team_id = get_team_id()
    if team_id is None:
        return pd.DataFrame()
    matches_data = load_json("matches.json")
    return build_matches_df(matches_data, team_id)


def get_standings_table() -> pd.DataFrame:
    standings = load_json("standings.json")
    rows = []
    for table in standings.get("standings", []):
        if table.get("type") != "TOTAL":
            continue
        for row in table.get("table", []):
            rows.append(
                {
                    "順位": row["position"],
                    "チーム": row["team"]["name"],
                    "試合": row["playedGames"],
                    "勝": row["won"],
                    "分": row["draw"],
                    "敗": row["lost"],
                    "得点": row["goalsFor"],
                    "失点": row["goalsAgainst"],
                    "得失差": row["goalDifference"],
                    "勝点": row["points"],
                }
            )
    return pd.DataFrame(rows)


def get_scorers_df() -> pd.DataFrame:
    data = load_json("scorers.json")
    rows = []
    for s in data.get("scorers", []):
        p = s.get("player", {})
        t = s.get("team", {})
        rows.append(
            {
                "選手": p.get("name", ""),
                "チーム": t.get("name", ""),
                "得点": s.get("goals", 0),
                "アシスト": s.get("assists") or 0,
                "出場": s.get("playedMatches", 0),
            }
        )
    return pd.DataFrame(rows)


# ── ヘルパー ──────────────────────────────────────────────────────────────────

def highlight_jubilo(df: pd.DataFrame) -> pd.DataFrame.style:
    team_id = get_team_id()
    if team_id is None:
        return df.style
    standings = load_json("standings.json")
    jubilo_name = None
    for table in standings.get("standings", []):
        for row in table.get("table", []):
            if row["team"]["id"] == team_id:
                jubilo_name = row["team"]["name"]
                break
    if jubilo_name is None:
        return df.style

    def highlight(row):
        return ["background-color: #003B73; color: white"] * len(row) if row["チーム"] == jubilo_name else [""] * len(row)

    return df.style.apply(highlight, axis=1)


# ── メイン ────────────────────────────────────────────────────────────────────

st.title("⚽ ジュビロ磐田 ダッシュボード")

meta = load_json("meta.json")
season = meta.get("season", "—")
st.caption(f"シーズン: {season}　　データソース: football-data.org")

if not (DATA_DIR / "matches.json").exists():
    st.warning(
        "データファイルが見つかりません。`python scripts/fetch_all.py` を実行してください。",
        icon="⚠️",
    )
    st.stop()

matches_df = get_matches_df()
standings_df = get_standings_table()

tab1, tab2, tab3 = st.tabs(["🏆 チーム概況", "👤 選手スタッツ", "⚔️ 対戦相手分析"])


# ─────────────────────────────────────
# Tab 1: チーム概況
# ─────────────────────────────────────
with tab1:
    col_left, col_right = st.columns([1, 2])

    # 順位表
    with col_left:
        st.subheader("順位表")
        if not standings_df.empty:
            st.dataframe(highlight_jubilo(standings_df), use_container_width=True, hide_index=True)
        else:
            st.info("データなし")

    with col_right:
        # 直近試合スコアカード
        st.subheader("直近の試合")
        if not matches_df.empty:
            last = matches_df.iloc[-1]
            venue = "🏠 ホーム" if last["is_home"] else "✈️ アウェイ"
            result_color = {"W": "🟢", "D": "🟡", "L": "🔴"}.get(last["result"], "⚪")
            st.markdown(
                f"{result_color} **{last['date'].strftime('%Y/%m/%d')}** {venue}　"
                f"vs **{last['opponent_name']}**　"
                f"**{int(last['goals_for'])} - {int(last['goals_against'])}**"
            )

        # フォーム折れ線 (直近5試合累積勝点)
        st.subheader("直近5試合 フォーム")
        if not matches_df.empty:
            form_df = compute_form(matches_df, n=5)
            fig = px.line(
                form_df,
                x="matchday",
                y="cumulative_points",
                markers=True,
                labels={"matchday": "節", "cumulative_points": "累積勝点"},
                color_discrete_sequence=["#003B73"],
            )
            fig.update_traces(
                customdata=form_df[["opponent_name", "result"]].values,
                hovertemplate="第%{x}節 vs %{customdata[0]}<br>結果: %{customdata[1]}<br>累積勝点: %{y}",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("データなし")

    # 得点/失点推移
    st.subheader("節ごとの得点 / 失点")
    if not matches_df.empty:
        goal_df = compute_matchday_goals(matches_df)
        fig2 = go.Figure()
        fig2.add_bar(x=goal_df["matchday"], y=goal_df["goals_for"], name="得点", marker_color="#003B73")
        fig2.add_bar(x=goal_df["matchday"], y=goal_df["goals_against"], name="失点", marker_color="#B0B0B0")
        fig2.update_layout(barmode="group", xaxis_title="節", yaxis_title="ゴール数")
        st.plotly_chart(fig2, use_container_width=True)

    # ホーム/アウェイ
    st.subheader("ホーム / アウェイ 別成績")
    if not matches_df.empty:
        ha_df = compute_home_away(matches_df)
        fig3 = px.bar(
            ha_df.melt(id_vars="venue", value_vars=["W", "D", "L"], var_name="結果", value_name="試合数"),
            x="venue",
            y="試合数",
            color="結果",
            color_discrete_map={"W": "#003B73", "D": "#A0A0A0", "L": "#E0E0E0"},
            barmode="stack",
            labels={"venue": ""},
        )
        st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────
# Tab 2: 選手スタッツ
# ─────────────────────────────────────
with tab2:
    scorers_df = get_scorers_df()

    st.subheader("得点 + アシスト ランキング (リーグ全体 Top 10)")
    if not scorers_df.empty:
        top10 = scorers_df.head(10).copy()
        top10["G+A"] = top10["得点"] + top10["アシスト"]
        fig_s = px.bar(
            top10,
            x="選手",
            y=["得点", "アシスト"],
            barmode="stack",
            color_discrete_map={"得点": "#003B73", "アシスト": "#7BAFD4"},
            labels={"value": "数", "variable": "種別"},
        )
        fig_s.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_s, use_container_width=True)

        st.subheader("得点ランキング 詳細")
        st.dataframe(top10[["選手", "チーム", "得点", "アシスト", "出場"]], use_container_width=True, hide_index=True)
    else:
        st.info("データなし")

    # ジュビロ選手フォーカス (試合データから計算)
    if not matches_df.empty and not scorers_df.empty:
        st.subheader("ジュビロ選手 フォーカス")
        meta_data = load_json("standings.json")
        jubilo_scorers = scorers_df[scorers_df["チーム"].str.contains("Jubilo", case=False, na=False)]
        if not jubilo_scorers.empty:
            st.dataframe(jubilo_scorers, use_container_width=True, hide_index=True)
        else:
            st.info("ジュビロ選手の得点データなし (チーム名でフィルタ中)")


# ─────────────────────────────────────
# Tab 3: 対戦相手分析
# ─────────────────────────────────────
with tab3:
    if matches_df.empty:
        st.info("データなし")
    else:
        opp_df = compute_opponent_record(matches_df)

        st.subheader("対戦相手別 勝率ヒートマップ")
        if not opp_df.empty:
            fig_h = px.bar(
                opp_df.sort_values("win_rate", ascending=True),
                x="win_rate",
                y="opponent_name",
                orientation="h",
                color="win_rate",
                color_continuous_scale=["#E0E0E0", "#003B73"],
                range_color=[0, 1],
                labels={"win_rate": "勝率", "opponent_name": "対戦相手"},
            )
            fig_h.update_layout(yaxis_title="", coloraxis_showscale=False)
            st.plotly_chart(fig_h, use_container_width=True)

        st.subheader("対戦相手別 得失点差")
        if not opp_df.empty:
            opp_sorted = opp_df.sort_values("goal_diff", ascending=False)
            colors = ["#003B73" if v >= 0 else "#D9534F" for v in opp_sorted["goal_diff"]]
            fig_gd = go.Figure(
                go.Bar(
                    x=opp_sorted["opponent_name"],
                    y=opp_sorted["goal_diff"],
                    marker_color=colors,
                )
            )
            fig_gd.update_layout(xaxis_tickangle=-45, xaxis_title="", yaxis_title="得失点差")
            st.plotly_chart(fig_gd, use_container_width=True)

        st.subheader("対戦相手別 詳細")
        st.dataframe(
            opp_df[["opponent_name", "played", "W", "D", "L", "win_rate", "goal_diff"]].rename(
                columns={"opponent_name": "相手", "played": "試合", "win_rate": "勝率", "goal_diff": "得失差"}
            ),
            use_container_width=True,
            hide_index=True,
        )
