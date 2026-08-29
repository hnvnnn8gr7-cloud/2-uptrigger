from datetime import datetime, timezone
import math
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
# 2. OUTPLAYED-STYLE FTA% POISSON PROBABILITY MODEL
# ---------------------------------------------------------
def calculate_poisson_fta(back_odds, total_goals_lambda=2.65, is_home=True):
    """Calculates dynamic FTA% (Full-Time Analysis Payout Probability)

    using implied match odds and Poisson goal distribution model.
    """
    if not back_odds or back_odds <= 1.0:
        return 1.50  # Baseline fallback FTA%

    # Implied win probability from bookie odds
    implied_win_prob = 1.0 / back_odds

    # Expected team goals based on implied probability and average match total
    home_bias = 1.15 if is_home else 0.88
    team_exp_goals = max(
        0.4, (implied_win_prob * total_goals_lambda) * home_bias
    )

    # Poisson probability of scoring 2+ goals in a match P(X >= 2)
    p0 = math.exp(-team_exp_goals)
    p1 = team_exp_goals * math.exp(-team_exp_goals)
    p_2plus_goals = 1.0 - (p0 + p1)

    # FTA% adjustment for 2UP early payout probability
    fta_pct = round(p_2plus_goals * implied_win_prob * 100, 2)
    return max(0.50, min(fta_pct, 8.50))


def parse_kickoff_datetime(iso_str):
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None


def format_kickoff_time(dt):
    if not dt:
        return "TBD"
    return dt.strftime("%d/%m/%Y | %H:%M")


# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS & API KEY
# ---------------------------------------------------------
st.sidebar.title("⚙️ Outplayed 2UP Filters")

secret_api_key = st.secrets.get("ODDS_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "The-Odds-API Key",
    value=secret_api_key,
    type="password",
    help="Enter your API key here if not set in Streamlit Secrets.",
)

st.sidebar.divider()

min_ev_filter = st.sidebar.slider(
    "Minimum EV % (Base 100%)", 90.0, 115.0, 98.0, 0.5
)
search_query = st.sidebar.text_input("Search Team or League", "")


# ---------------------------------------------------------
# 4. FETCH LIVE ODDS (H2H MATCH WINNER)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_live_fixtures(api_key):
    if not api_key:
        return []

    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={api_key}&regions=uk,eu&markets=h2h&oddsFormat=decimal"
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
cards_data = []

now_utc = datetime.now(timezone.utc)

if raw_fixtures:
    for match in raw_fixtures:
        commence_raw = match.get("commence_time", "")
        dt_kickoff = parse_kickoff_datetime(commence_raw)

        # Filter out matches that already started
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
            bookie_name = "Bookie"
            exchange_name = "Exchange"

            for b in bookies:
                b_title = b.get("title", "")
                is_exchange = any(
                    ex in b.get("key", "").lower()
                    for ex in ["ex", "smarkets", "matchbook", "betfair"]
                )

                for m in b.get("markets", []):
                    if m["key"] == "h2h":
                        for outcome in m.get("outcomes", []):
                            if outcome["name"] == team_name:
                                price = outcome["price"]
                                if is_exchange and (
                                    lay_odds is None or price < lay_odds
                                ):
                                    lay_odds = price
                                    exchange_name = b_title
                                elif not is_exchange and (
                                    back_odds is None or price > back_odds
                                ):
                                    back_odds = price
                                    bookie_name = b_title

            # Lay odds fallback estimation if exchange unlisted
            if back_odds and not lay_odds:
                lay_odds = round(back_odds * 1.02, 2)
                exchange_name = "Betfair Ex"

            if back_odds and lay_odds:
                is_home_bool = side == "Home"
                fta_pct = calculate_poisson_fta(
                    back_odds, is_home=is_home_bool
                )

                # Outplayed 100%+ EV Formula: (Back Odds / Lay Odds * (1 + FTA%))
                ev_pct = round(
                    ((back_odds / lay_odds) + (fta_pct / 100)) * 100, 1
                )

                cards_data.append(
                    {
                        "id": f"{home_team}_vs_{away_team}_{side.lower()}",
                        "kickoff": kickoff_fmt,
                        "team": team_name,
                        "match": f"{home_team} vs {away_team}",
                        "league": league,
                        "back_odds": back_odds,
                        "lay_odds": lay_odds,
                        "bookie": bookie_name,
                        "exchange": exchange_name,
                        "fta_pct": fta_pct,
                        "ev_pct": ev_pct,
                    }
                )

# Sort fixtures by highest EV% first
cards_data = sorted(cards_data, key=lambda x: x["ev_pct"], reverse=True)

# ---------------------------------------------------------
# 5. DASHBOARD LAYOUT (OUTPLAYED MASTER CARDS STYLE)
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["⚡ Outplayed 2UP Master", "📊 Performance Tracker"])

with tab1:
    st.title("2UP Opportunities")

    if not api_key_input:
        st.warning(
            "⚠️ Please enter your Odds API Key in the sidebar or setup Secrets."
        )
    elif not cards_data:
        st.info("No upcoming 2UP opportunities found.")
    else:
        filtered_cards = [
            c
            for c in cards_data
            if c["ev_pct"] >= min_ev_filter
            and (
                search_query.lower() in c["match"].lower()
                or search_query.lower() in c["league"].lower()
                or search_query.lower() in c["team"].lower()
            )
        ]

        if not filtered_cards:
            st.info("No fixtures matched your selected filters.")
        else:
            for item in filtered_cards:
                # Custom CSS Card Container mirroring Outplayed layout
                st.markdown(
                    f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 12px; padding: 16px; margin-bottom: 16px; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="color: #666; font-size: 14px;">🕒 {item['kickoff']}</span>
                        <span style="background-color: #00c853; color: white; padding: 4px 12px; border-radius: 16px; font-weight: bold; font-size: 14px;">
                            {item['ev_pct']}% EV
                        </span>
                    </div>
                    <div style="font-size: 20px; font-weight: bold; color: #111; margin-bottom: 2px;">{item['team']}</div>
                    <div style="color: #777; font-size: 14px; margin-bottom: 16px;">{item['league']} ({item['match']})</div>
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <div style="flex: 1; background: #f5f5f5; padding: 8px 12px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 11px; color: #666;">Bookie Odds</div>
                            <div style="font-size: 16px; font-weight: bold; color: #009688;">{item['back_odds']}</div>
                            <div style="font-size: 10px; color: #444; margin-top: 2px;"><b>{item['bookie']}</b></div>
                        </div>
                        <div style="flex: 1; background: #f5f5f5; padding: 8px 12px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 11px; color: #666;">Lay Odds</div>
                            <div style="font-size: 16px; font-weight: bold; color: #d32f2f;">{item['lay_odds']}</div>
                            <div style="font-size: 10px; color: #444; margin-top: 2px;"><b>{item['exchange']}</b></div>
                        </div>
                        <div style="flex: 1; background: #f5f5f5; padding: 8px 12px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 11px; color: #666;">FTA%</div>
                            <div style="font-size: 16px; font-weight: bold; color: #00b0ff;">{item['fta_pct']}%</div>
                            <div style="font-size: 10px; color: #444; margin-top: 2px;">Payout Prob</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                col_b1, col_b2 = st.columns([5, 1])
                with col_b2:
                    already_tracked = any(
                        t["id"] == item["id"]
                        for t in st.session_state["tracked_bets"]
                    )
                    if already_tracked:
                        st.button(
                            "Tracked ✓", key=f"btn_{item['id']}", disabled=True
                        )
                    else:
                        if st.button("Track Bet 📌", key=f"btn_{item['id']}"):
                            st.session_state["tracked_bets"].append(
                                {
                                    "id": item["id"],
                                    "match": item["match"],
                                    "team": item["team"],
                                    "kickoff": item["kickoff"],
                                    "back_odds": item["back_odds"],
                                    "lay_odds": item["lay_odds"],
                                    "ev_status": f"{item['ev_pct']}% EV (FTA: {item['fta_pct']}%)",
                                    "result": "Pending ⏳",
                                }
                            )
                            st.rerun()
                st.divider()

with tab2:
    st.header("Tracked Performance Dashboard")

    tracked = st.session_state["tracked_bets"]
    if not tracked:
        st.info("No bets tracked yet. Click **Track Bet 📌** on any card.")
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
