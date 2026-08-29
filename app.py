from datetime import datetime, timezone
import io
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="2UP Master Finder & Tracker", page_icon="⚽", layout="wide"
)

# ---------------------------------------------------------
# 1. SESSION STATE INITIALIZATION
# ---------------------------------------------------------
if "tracked_bets" not in st.session_state:
    st.session_state["tracked_bets"] = []


# ---------------------------------------------------------
# 2. LOAD HISTORICAL DATASET
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def load_historical_stats():
    try:
        df = pd.read_csv("2up_multi_league_dataset.csv")
        df["clean_team"] = (
            df["trigger_team"]
            .astype(str)
            .str.lower()
            .str.replace(r"[^a-z0-9]", "", regex=True)
        )

        stats = (
            df.groupby("clean_team")
            .agg(
                total_2ups=("2up_triggered", "sum"),
                total_comebacks=("comeback_occurred", "sum"),
            )
            .reset_index()
        )

        def calc_pct(row):
            if row["total_2ups"] < 3:
                return 0.125
            return row["total_comebacks"] / row["total_2ups"]

        stats["turnaround_pct"] = stats.apply(calc_pct, axis=1)
        return dict(zip(stats["clean_team"], stats["turnaround_pct"]))
    except Exception:
        return {}


stats_dict = load_historical_stats()


def get_turnaround(team_name):
    clean = (
        pd.Series([team_name])
        .str.lower()
        .str.replace(r"[^a-z0-9]", "", regex=True)
        .iloc[0]
    )
    return stats_dict.get(clean, 0.125)


def parse_kickoff_datetime(iso_str):
    """Parses ISO string to UTC datetime object."""
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None


def format_kickoff_time(dt):
    """Formats datetime object into readable string."""
    if not dt:
        return "TBD"
    return dt.strftime("%a %d %b %H:%M")


# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS & API KEY
# ---------------------------------------------------------
st.sidebar.title("⚙️ 2UP Master Filters")

secret_api_key = st.secrets.get("ODDS_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "The-Odds-API Key",
    value=secret_api_key,
    type="password",
    help="Enter your API key here if not set in Streamlit Secrets.",
)

st.sidebar.divider()

selected_statuses = st.sidebar.multiselect(
    "Filter Rating",
    ["🟢 EXCELLENT", "🟡 GOOD", "⚪ STANDARD"],
    default=["🟢 EXCELLENT", "🟡 GOOD", "⚪ STANDARD"],
)

min_ev_filter = st.sidebar.slider("Minimum EV %", -5.0, 30.0, 0.0, 0.5)
search_query = st.sidebar.text_input("Search Team or League", "")


# ---------------------------------------------------------
# 4. FETCH AND PROCESS 2UP MATCH DATA
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_live_fixtures(api_key):
    if not api_key:
        return []

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={api_key}&regions=uk&markets=h2h&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.error("⚠️ Invalid API Key.")
    except Exception as e:
        st.error(f"Error fetching odds: {e}")
    return []


raw_fixtures = fetch_live_fixtures(api_key_input)
table_rows = []

# Get current UTC time to filter out started/past matches
now_utc = datetime.now(timezone.utc)

if raw_fixtures:
    for match in raw_fixtures:
        commence_raw = match.get("commence_time", "")
        dt_kickoff = parse_kickoff_datetime(commence_raw)

        # Skip match if it has already kicked off
        if dt_kickoff and dt_kickoff <= now_utc:
            continue

        home_team = match.get("home_team", "Unknown")
        away_team = match.get("away_team", "Unknown")
        league = match.get("sport_title", "Soccer")
        kickoff_fmt = format_kickoff_time(dt_kickoff)

        bookies = match.get("bookmakers", [])
        if not bookies:
            continue

        for side, team_name in [("Home", home_team), ("Away", away_team)]:
            back_odds = None
            lay_odds = None

            for b in bookies:
                is_exchange = b.get("key") in [
                    "betfair_ex_uk",
                    "smarkets",
                    "matchbook",
                ]
                for m in b.get("markets", []):
                    if m["key"] == "h2h":
                        for outcome in m.get("outcomes", []):
                            if outcome["name"] == team_name:
                                price = outcome["price"]
                                if is_exchange and (
                                    lay_odds is None or price < lay_odds
                                ):
                                    lay_odds = price
                                elif not is_exchange and (
                                    back_odds is None or price > back_odds
                                ):
                                    back_odds = price

            if back_odds and not lay_odds:
                lay_odds = round(back_odds * 1.02, 2)

            if back_odds and lay_odds:
                turnaround = get_turnaround(team_name)

                # Qualifying Loss Percentage
                ql_pct = ((lay_odds - back_odds) / back_odds) * 100

                # Expected Value %
                ev_val = (
                    (turnaround * back_odds) / (1 + (ql_pct / 100))
                ) - 1
                ev_pct = round(ev_val * 100, 1)

                if ev_pct >= 15.0:
                    badge_type = "🟢 EXCELLENT"
                elif ev_pct >= 5.0:
                    badge_type = "🟡 GOOD"
                else:
                    badge_type = "⚪ STANDARD"

                table_rows.append(
                    {
                        "Track": False,
                        "id": f"{home_team}_vs_{away_team}_{side.lower()}",
                        "Rating": badge_type,
                        "Kickoff": kickoff_fmt,
                        "Match": f"{home_team} vs {away_team}",
                        "Selection": f"{team_name} ({side[0]})",
                        "League": league,
                        "Back Odds": back_odds,
                        "Lay Odds": lay_odds,
                        "QL %": f"{round(ql_pct, 1)}%",
                        "Turnaround %": f"{round(turnaround * 100, 1)}%",
                        "EV %": ev_pct,
                    }
                )

# ---------------------------------------------------------
# 5. DASHBOARD LAYOUT
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["⚡ 2UP Master Odds", "📊 Performance Tracker"])

with tab1:
    st.title("2UP Master Opportunities")

    if not api_key_input:
        st.warning(
            "⚠️ Please enter your Odds API Key in the sidebar or setup Secrets to load match odds."
        )
    elif not table_rows:
        st.info("No upcoming 2UP opportunities found.")
    else:
        df_master = pd.DataFrame(table_rows)

        filtered_df = df_master[
            (df_master["Rating"].isin(selected_statuses))
            & (df_master["EV %"] >= min_ev_filter)
            & (
                df_master["Match"].str.contains(search_query, case=False)
                | df_master["League"].str.contains(search_query, case=False)
                | df_master["Selection"].str.contains(search_query, case=False)
            )
        ]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Upcoming Fixtures", len(filtered_df))
        c2.metric(
            "Excellent Matches",
            len(filtered_df[filtered_df["Rating"] == "🟢 EXCELLENT"]),
        )
        c3.metric(
            "Avg EV %",
            (
                f"{round(filtered_df['EV %'].mean(), 1)}%"
                if not filtered_df.empty
                else "0.0%"
            ),
        )
        c4.metric(
            "Max EV %",
            (
                f"+{filtered_df['EV %'].max()}%"
                if not filtered_df.empty
                else "0.0%"
            ),
        )

        st.divider()

        if filtered_df.empty:
            st.info("No upcoming fixtures matched your selected filters.")
        else:
            edited_df = st.data_editor(
                filtered_df,
                column_config={
                    "Track": st.column_config.CheckboxColumn(
                        "Track Bet",
                        help="Check to log bet to tracker",
                        default=False,
                    ),
                    "id": None,
                    "Rating": st.column_config.TextColumn(
                        "Rating", width="medium"
                    ),
                    "Kickoff": st.column_config.TextColumn(
                        "Kickoff", width="small"
                    ),
                    "Match": st.column_config.TextColumn(
                        "Fixture", width="medium"
                    ),
                    "Selection": st.column_config.TextColumn(
                        "Selection", width="medium"
                    ),
                    "League": st.column_config.TextColumn(
                        "League", width="medium"
                    ),
                    "Back Odds": st.column_config.NumberColumn(
                        "Back Odds", format="%.2f"
                    ),
                    "Lay Odds": st.column_config.NumberColumn(
                        "Lay Odds", format="%.2f"
                    ),
                    "QL %": st.column_config.TextColumn("QL %"),
                    "Turnaround %": st.column_config.TextColumn("Turnaround"),
                    "EV %": st.column_config.NumberColumn(
                        "EV %", format="+%.1f%%"
                    ),
                },
                disabled=[
                    "id",
                    "Rating",
                    "Kickoff",
                    "Match",
                    "Selection",
                    "League",
                    "Back Odds",
                    "Lay Odds",
                    "QL %",
                    "Turnaround %",
                    "EV %",
                ],
                hide_index=True,
                use_container_width=True,
            )

            if st.button("📌 Save Checked Bets to Tracker"):
                new_tracked_count = 0
                for _, row in edited_df.iterrows():
                    if row["Track"]:
                        already_exists = any(
                            t["id"] == row["id"]
                            for t in st.session_state["tracked_bets"]
                        )
                        if not already_exists:
                            st.session_state["tracked_bets"].append(
                                {
                                    "id": row["id"],
                                    "match": row["Match"],
                                    "team": row["Selection"],
                                    "kickoff": row["Kickoff"],
                                    "back_odds": row["Back Odds"],
                                    "lay_odds": row["Lay Odds"],
                                    "ev_status": f"{row['Rating']} (+{row['EV %']}%)",
                                    "result": "Pending ⏳",
                                }
                            )
                            new_tracked_count += 1
                if new_tracked_count > 0:
                    st.success(
                        f"Added {new_tracked_count} new bet(s) to Tracker!"
                    )
                    st.rerun()
                else:
                    st.info(
                        "No new bets checked or selected bets were already tracked."
                    )

with tab2:
    st.header("Tracked Performance Dashboard")

    tracked = st.session_state["tracked_bets"]
    if not tracked:
        st.info(
            "No bets tracked yet. Check **Track Bet** in the master table and click Save."
        )
    else:
        total_bets = len(tracked)
        wins = sum(1 for b in tracked if b["result"] == "Won 🟢")
        losses = sum(1 for b in tracked if b["result"] == "Lost 🔴")
        pending = sum(1 for b in tracked if b["result"] == "Pending ⏳")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tracked", total_bets)
        m2.metric("Wins 🟢", wins)
        m3.metric("Losses 🔴", losses)
        m4.metric("Pending ⏳", pending)

        st.divider()

        for idx, item in enumerate(tracked):
            c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
            with c1:
                st.write(f"**{item['match']}**")
                st.caption(
                    f"Selected: {item['team']} | Back: {item.get('back_odds', 'N/A')} | Lay: {item.get('lay_odds', 'N/A')}"
                )
            with c2:
                st.write(f"**{item.get('ev_status', '')}**")
            with c3:
                new_res = st.selectbox(
                    "Set Outcome",
                    ["Pending ⏳", "Won 🟢", "Lost 🔴"],
                    index=["Pending ⏳", "Won 🟢", "Lost 🔴"].index(
                        item["result"]
                    ),
                    key=f"res_{item['id']}",
                )
                st.session_state["tracked_bets"][idx]["result"] = new_res
            with c4:
                if st.button("Remove 🗑️", key=f"del_{item['id']}"):
                    st.session_state["tracked_bets"].pop(idx)
                    st.rerun()
            st.divider()
