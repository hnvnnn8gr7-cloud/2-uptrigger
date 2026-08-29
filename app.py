import pandas as pd
import requests
import streamlit as st

# --- PAGE CONFIGURATION FOR MOBILE ---
st.set_page_config(
    page_title="2UP Turnaround Finder",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
st.caption("Live Match Ratings & Historical Comeback Probabilities")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ App Settings")

# Retrieve API key from Streamlit Secrets automatically; fallback to input field if missing
if "ODDS_API_KEY" in st.secrets:
    API_KEY = st.secrets["ODDS_API_KEY"]
    st.sidebar.success("🔑 API Key loaded automatically!")
else:
    API_KEY = st.sidebar.text_input(
        "The-Odds-API Key",
        value="",
        type="password",
        help="Add ODDS_API_KEY to Streamlit Secrets to skip this step.",
    )

DEFAULT_STAKE = st.sidebar.number_input(
    "Default Back Stake (£)", value=100.0, step=10.0
)
COMMISSION = (
    st.sidebar.slider("Exchange Commission (%)", 0.0, 5.0, 2.0, 0.5) / 100.0
)


# --- STEP 1: LOAD & PROCESS HISTORICAL SCRAPED DATASET ---
@st.cache_data
def load_historical_ratings():
    try:
        df = pd.read_csv("2up_multi_league_dataset.csv")

        # Filter matches where a 2-goal lead was triggered
        triggered_df = df[df["2up_triggered"] == True].copy()

        # Aggregate total 2UP triggers and comebacks conceded/allowed
        stats = (
            triggered_df.groupby("trigger_team")
            .agg(
                total_2ups=("2up_triggered", "count"),
                comebacks=("comeback_occurred", "sum"),
            )
            .reset_index()
        )

        stats["turnaround_pct"] = (stats["comebacks"] / stats["total_2ups"]) * 100
        global_avg = (
            triggered_df["comeback_occurred"].mean() * 100
            if len(triggered_df) > 0
            else 12.5
        )

        return stats, round(global_avg, 1)
    except Exception:
        # Fallback if CSV dataset is missing from repository
        return pd.DataFrame(), 12.5


stats_df, GLOBAL_AVG = load_historical_ratings()


def get_turnaround_pct(team_name: str) -> tuple[float, int]:
    """Returns (turnaround_pct, total_2ups) for a team."""
    if not stats_df.empty and team_name in stats_df["trigger_team"].values:
        row = stats_df[stats_df["trigger_team"] == team_name].iloc[0]
        return round(row["turnaround_pct"], 1), int(row["total_2ups"])
    return GLOBAL_AVG, 0


# --- STEP 2: QUALIFYING LOSS (QL) & LAY STAKE MATH ---
def calculate_matched_bet(back_stake: float, back_odds: float, lay_odds: float):
    if lay_odds <= COMMISSION:
        return 0.0, 0.0

    lay_stake = (back_stake * back_odds) / (lay_odds - COMMISSION)
    ql = back_stake - (lay_stake * (1.0 - COMMISSION))
    return round(lay_stake, 2), round(ql, 2)


# --- STEP 3: PARSE LIVE ODDS (OUTPLAYED TARGET LEAGUES) ---
def fetch_odds():
    if not API_KEY:
        st.warning(
            "⚠️ API Key missing. Add `ODDS_API_KEY` to Streamlit Secrets or enter it in the sidebar."
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
        ]

    target_sports = [
        "soccer_epl",
        "soccer_efl_champ",
        "soccer_england_league1",
        "soccer_england_league2",
        "soccer_germany_bundesliga",
        "soccer_germany_bundesliga2",
        "soccer_spain_la_liga",
        "soccer_italy_serie_a",
        "soccer_france_ligue_one",
        "soccer_netherlands_eredivisie",
        "soccer_belgium_first_div",
        "soccer_uefa_champs_league",
        "soccer_uefa_europa_league",
    ]

    matches = []

    for sport_key in target_sports:
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=uk&markets=h2h&bookmakers=bet365,smarkets,betfair_ex,skybet,ladbrokes_uk"

        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue

            data = res.json()

            for game in data:
                home = game.get("home_team")
                away = game.get("away_team")
                league = game.get("sport_title", "Football")

                for team in [home, away]:
                    back_price = None
                    lay_price = None

                    for b in game.get("bookmakers", []):
                        if b["key"] in [
                            "bet365",
                            "skybet",
                            "ladbrokes_uk",
                        ] and not back_price:
                            for outcome in b["markets"][0]["outcomes"]:
                                if outcome["name"] == team:
                                    back_price = float(outcome["price"])

                        if b["key"] in [
                            "smarkets",
                            "betfair_ex",
                        ] and not lay_price:
                            for outcome in b["markets"][0]["outcomes"]:
                                if outcome["name"] == team:
                                    lay_price = float(outcome["price"])

                    if back_price and not lay_price:
                        lay_price = round(back_price * 1.03, 2)

                    if back_price and lay_price:
                        matches.append(
                            {
                                "home": home,
                                "away": away,
                                "league": league,
                                "selection": team,
                                "back_odds": back_price,
                                "lay_odds": lay_price,
                            }
                        )
        except Exception:
            continue

    if not matches:
        st.info("No active matches found across target leagues right now.")

    return matches


# --- STEP 4: DASHBOARD & CALCULATOR TABS ---
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

        ql_pct = (abs(ql) / DEFAULT_STAKE) * 100

        if turnaround_pct >= 14.0 and ql_pct <= 1.5:
            rating = "🟢 EXCELLENT EV"
        elif turnaround_pct >= 11.0 and ql_pct <= 2.5:
            rating = "🟡 GOOD EV"
        else:
            rating = "⚪ POOR EV"

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
