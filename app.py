import pandas as pd
import requests
import streamlit as st

# Page Configuration for Mobile
st.set_page_config(
    page_title="2UP Turnaround Finder",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom Styling to mimic a native iPhone app
st.markdown(
    """
    <style>
    .stApp { padding-top: 1rem; }
    .metric-card {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚽ 2UP Turnaround Finder")
st.caption("Live Odds & Historical Comeback Ratings")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ App Settings")
API_KEY = st.sidebar.text_input(
    "The-Odds-API Key",
    value="",
    type="password",
    help="Get a free key at the-odds-api.com",
)
DEFAULT_STAKE = st.sidebar.number_input(
    "Default Back Stake (£)", value=100.0, step=10.0
)
COMMISSION = (
    st.sidebar.slider("Exchange Commission (%)", 0.0, 5.0, 2.0, 0.5) / 100.0
)


# --- STEP 1: HISTORICAL DATA PROCESSING ---
@st.cache_data
def load_historical_ratings():
    try:
        df = pd.read_csv("2up_multi_league_dataset.csv")

        # Filter only matches where 2UP triggered
        triggered_df = df[df["2up_triggered"] == True].copy()

        # Group by trigger_team to find total 2UPs and comebacks conceded/made
        stats = (
            triggered_df.groupby("trigger_team")
            .agg(
                total_2ups=("2up_triggered", "count"),
                comebacks=("comeback_occurred", "sum"),
            )
            .reset_index()
        )

        stats["turnaround_pct"] = (stats["comebacks"] / stats["total_2ups"]) * 100

        # Global average fallback
        global_avg = (
            triggered_df["comeback_occurred"].mean() * 100
            if len(triggered_df) > 0
            else 12.5
        )

        return stats, round(global_avg, 1)
    except Exception as e:
        # Fallback if CSV is not found in GitHub repo yet
        return pd.DataFrame(), 12.5


stats_df, GLOBAL_AVG = load_historical_ratings()


def get_turnaround_pct(team_name: str) -> tuple[float, int]:
    """Returns (turnaround_pct, total_2ups) for a team."""
    if not stats_df.empty and team_name in stats_df["trigger_team"].values:
        row = stats_df[stats_df["trigger_team"] == team_name].iloc[0]
        return round(row["turnaround_pct"], 1), int(row["total_2ups"])
    return GLOBAL_AVG, 0


# --- STEP 2: QUALIFYING LOSS (QL) CALCULATOR ---
def calculate_matched_bet(back_stake: float, back_odds: float, lay_odds: float):
    if lay_odds <= COMMISSION:
        return 0.0, 0.0

    # Calculate optimal lay stake
    lay_stake = (back_stake * back_odds) / (lay_odds - COMMISSION)

    # Calculate Qualifying Loss
    ql = back_stake - (lay_stake * (1.0 - COMMISSION))
    return round(lay_stake, 2), round(ql, 2)


# --- STEP 3: FETCH LIVE ODDS ---
def fetch_odds():
    if not API_KEY:
        st.warning(
            "⚠️ Enter your API Key in the sidebar to load live odds. Showing mock data below:"
        )
        return [
            {
                "home": "Leeds",
                "away": "Leicester",
                "league": "EFL Championship",
                "selection": "Leeds",
                "back_odds": 2.80,
                "lay_odds": 2.84,
            },
            {
                "home": "Augsburg",
                "away": "Stuttgart",
                "league": "Bundesliga",
                "selection": "Augsburg",
                "back_odds": 3.75,
                "lay_odds": 3.86,
            },
            {
                "home": "Plymouth",
                "away": "Ipswich",
                "league": "EFL Championship",
                "selection": "Ipswich",
                "back_odds": 1.95,
                "lay_odds": 1.98,
            },
        ]

    url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?apiKey={API_KEY}&regions=uk&markets=h2h&bookmakers=bet365,smarkets,betfair_ex"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        matches = []
        return matches
    except Exception as e:
        st.error(f"Error fetching odds: {e}")
        return []


# --- STEP 4: RENDER MOBILE DASHBOARD ---
matches = fetch_odds()

tab1, tab2 = st.tabs(["🔥 Today's Matches", "🧮 2UP Stake Calculator"])

with tab1:
    st.subheader(f"Matched Targets ({len(matches)})")

    for m in matches:
        team = m["selection"]
        turnaround_pct, total_games = get_turnaround_pct(team)
        lay_stake, ql = calculate_matched_bet(
            DEFAULT_STAKE, m["back_odds"], m["lay_odds"]
        )

        # Rating Logic
        ql_pct = (abs(ql) / DEFAULT_STAKE) * 100
        if turnaround_pct >= 14.0 and ql_pct <= 1.5:
            rating = "🟢 EXCELLENT EV"
        elif turnaround_pct >= 11.0 and ql_pct <= 2.5:
            rating = "🟡 GOOD EV"
        else:
            rating = "⚪ POOR EV"

        # Display Card
        with st.container():
            st.markdown(f"### {m['home']} vs {m['away']}")
            st.caption(f"**{m['league']}** | Selection: **{team}** ({rating})")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Back / Lay",
                    f"{m['back_odds']} / {m['lay_odds']}",
                )
            with c2:
                st.metric(
                    "Qualifying Loss",
                    f"-£{abs(ql):.2f}",
                    delta=f"-{ql_pct:.1f}%",
                    delta_color="inverse",
                )
            with c3:
                sample_text = (
                    f"{total_games} games sample"
                    if total_games > 0
                    else "Global Avg"
                )
                st.metric(
                    "Turnaround %",
                    f"{turnaround_pct}%",
                    help=sample_text,
                )

            st.divider()

with tab2:
    st.subheader("Manual Match Calculator")
    calc_back_stake = st.number_input(
        "Back Stake (£)", value=DEFAULT_STAKE, key="calc_bs"
    )
    calc_back_odds = st.number_input("Back Odds", value=2.50, key="calc_bo")
    calc_lay_odds = st.number_input("Lay Odds", value=2.54, key="calc_lo")

    lay_st, q_loss = calculate_matched_bet(
        calc_back_stake, calc_back_odds, calc_lay_odds
    )

    st.info(f"👉 **Lay Stake to Place:** £{lay_st:.2f}")
    st.error(f"📉 **Qualifying Loss:** -£{abs(q_loss):.2f}")
