from datetime import datetime
import io
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="2UP Value Finder & Tracker", page_icon="⚽", layout="wide"
)

# ---------------------------------------------------------
# 1. INITIALIZE TRACKER SESSION STATE
# ---------------------------------------------------------
if "tracked_bets" not in st.session_state:
    st.session_state["tracked_bets"] = []


# ---------------------------------------------------------
# 2. LOAD & PROCESS CSV STATS
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


# Helper function to format ISO 8601 UTC time to a readable Kick-Off string
def format_kickoff_time(iso_str):
    if not iso_str:
        return "TBD"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%a %d %b, %H:%M")
    except Exception:
        return iso_str


# ---------------------------------------------------------
# 3. FETCH LIVE ODDS FROM THE-ODDS-API
# ---------------------------------------------------------
API_KEY = st.secrets.get("ODDS_API_KEY", "")


@st.cache_data(ttl=300)
def fetch_live_fixtures():
    if not API_KEY:
        st.warning("⚠️ No ODDS_API_KEY set in secrets.")
        return []

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={API_KEY}&regions=uk&markets=h2h&oddsFormat=decimal"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Error fetching odds: {e}")
    return []


# ---------------------------------------------------------
# 4. PROCESS MATCH DATA & CALCULATE EV %
# ---------------------------------------------------------
raw_fixtures = fetch_live_fixtures()
processed_matches = []

QUALIFYING_LOSS_PCT = 0.015  # Default 1.5% QL benchmark

for match in raw_fixtures:
    home_team = match.get("home_team", "Unknown")
    away_team = match.get("away_team", "Unknown")
    league = match.get("sport_title", "Soccer")
    commence_raw = match.get("commence_time", "")
    kickoff_fmt = format_kickoff_time(commence_raw)

    bookies = match.get("bookmakers", [])
    if not bookies:
        continue

    home_back = None
    for b in bookies:
        for m in b.get("markets", []):
            if m["key"] == "h2h":
                for outcome in m.get("outcomes", []):
                    if outcome["name"] == home_team:
                        home_back = outcome["price"]

    if home_back:
        home_turnaround = get_turnaround(home_team)

        # Exact EV % Calculation
        ev_val = (
            (home_turnaround * home_back) / (1 + QUALIFYING_LOSS_PCT)
        ) - 1
        ev_pct = round(ev_val * 100, 1)

        # Format Status with EV Percentage Label
        if ev_pct >= 15.0:
            status = f"🟢 EXCELLENT (+{ev_pct}%)"
            badge_type = "🟢 EXCELLENT"
        elif ev_pct >= 5.0:
            status = f"🟡 GOOD (+{ev_pct}%)"
            badge_type = "🟡 GOOD"
        else:
            status = f"⚪ STANDARD ({'+' if ev_pct >= 0 else ''}{ev_pct}%)"
            badge_type = "⚪ STANDARD"

        processed_matches.append(
            {
                "id": f"{home_team}_vs_{away_team}_home",
                "match": f"{home_team} vs {away_team}",
                "team": home_team,
                "league": league,
                "kickoff": kickoff_fmt,
                "back_odds": home_back,
                "turnaround_pct": round(home_turnaround * 100, 1),
                "ev_pct": ev_pct,
                "ev_status": status,
                "badge_type": badge_type,
            }
        )

# ---------------------------------------------------------
# 5. SIDEBAR FILTERS
# ---------------------------------------------------------
st.sidebar.title("🔍 Match Filters")

selected_statuses = st.sidebar.multiselect(
    "Filter by EV Status",
    ["🟢 EXCELLENT", "🟡 GOOD", "⚪ STANDARD"],
    default=["🟢 EXCELLENT", "🟡 GOOD", "⚪ STANDARD"],
)

search_query = st.sidebar.text_input("Search Team / League", "")

# ---------------------------------------------------------
# 6. APP TABS: FIXTURES vs TRACKER
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["⚽ Live Fixtures", "📊 Performance Tracker"])

with tab1:
    st.header("Live 2UP EV Opportunities")

    filtered_matches = [
        m
        for m in processed_matches
        if m["badge_type"] in selected_statuses
        and (
            search_query.lower() in m["match"].lower()
            or search_query.lower() in m["league"].lower()
        )
    ]

    if not filtered_matches:
        st.info("No matches found matching your filters.")
    else:
        for m in filtered_matches:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 3, 2])
            with col1:
                st.write(f"**{m['match']}**")
                st.caption(f"🗓️ {m['kickoff']} | {m['league']}")
            with col2:
                st.write(f"Team: **{m['team']}**")
                st.caption(f"Odds: {m['back_odds']}")
            with col3:
                st.write(f"Turnaround: **{m['turnaround_pct']}%**")
            with col4:
                st.write(f"**{m['ev_status']}**")
            with col5:
                already_tracked = any(
                    t["id"] == m["id"] for t in st.session_state["tracked_bets"]
                )
                if already_tracked:
                    st.button("Tracked ✓", key=f"btn_{m['id']}", disabled=True)
                else:
                    if st.button("Track Bet 📌", key=f"btn_{m['id']}"):
                        st.session_state["tracked_bets"].append(
                            {
                                "id": m["id"],
                                "match": m["match"],
                                "team": m["team"],
                                "kickoff": m["kickoff"],
                                "status": m["ev_status"],
                                "result": "Pending ⏳",
                            }
                        )
                        st.rerun()
            st.divider()

with tab2:
    st.header("Tracked Performance Dashboard")

    tracked = st.session_state["tracked_bets"]
    if not tracked:
        st.info(
            "No bets tracked yet. Click **Track Bet 📌** on live fixtures to add them here."
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
                    f"Selected: {item['team']} | 🗓️ {item.get('kickoff', 'TBD')}"
                )
            with c2:
                st.write(f"**{item['status']}**")
            with c3:
                new_res = st.selectbox(
                    "Set Outcome",
                    ["Pending ⏳", "Won 🟢", "Lost 🔴"],
                    index=[
                        "Pending ⏳",
                        "Won 🟢",
                        "Lost 🔴",
                    ].index(item["result"]),
                    key=f"res_{item['id']}",
                )
                st.session_state["tracked_bets"][idx]["result"] = new_res
            with c4:
                if st.button("Remove 🗑️", key=f"del_{item['id']}"):
                    st.session_state["tracked_bets"].pop(idx)
                    st.rerun()
            st.divider()
