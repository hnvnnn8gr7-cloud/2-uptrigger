import streamlit as st
import pandas as pd

from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss,
    calculate_fta_profit,
    calculate_expected_profit,
    calculate_ev_percent,
    calculate_roi,
    calculate_win_rate
)

from database import (
    get_tracked_bets,
    get_performance_stats
)

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="2UP Master V3",
    page_icon="⚽",
    layout="wide"
)

# ==================================
# HEADER
# ==================================

st.title("⚽ 2UP Master V3")

st.caption(
    "Machine Learning Powered 2UP Opportunity Discovery & Tracking Platform"
)

# ==================================
# TABS
# ==================================

tab_opps, tab_tracking, tab_calc, tab_perf = st.tabs(
    [
        "⚡ Opportunities",
        "📌 Tracking",
        "🧮 Calculator",
        "📈 Performance"
    ]
)

# ==================================
# OPPORTUNITIES
# ==================================

with tab_opps:

    st.header(
        "⚡ Opportunities"
    )

    st.info(
        "Live Odds API integration will populate opportunities automatically."
    )

    st.markdown("---")

    st.subheader(
        "Opportunity Preview"
    )

    back_odds = st.number_input(
        "Back Odds",
        min_value=1.01,
        value=4.80,
        key="opp_back"
    )

    estimated_lay = round(
        back_odds * 1.05,
        2
    )

    lay_odds = st.number_input(
        "Lay Odds",
        min_value=1.01,
        value=float(estimated_lay),
        key="opp_lay"
    )

    commission = st.number_input(
        "Lay Commission %",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
        key="opp_commission"
    )

    fta_pct = st.number_input(
        "FTA %",
        min_value=0.0,
        value=2.5,
        key="opp_fta"
    )

    stake = st.number_input(
        "Stake (£)",
        min_value=1.0,
        value=40.0,
        key="opp_stake"
    )

    lay_stake = calculate_lay_stake(
        back_odds,
        lay_odds,
        stake,
        commission
    )

    liability = calculate_liability(
        lay_odds,
        lay_stake
    )

    qualifying_loss = (
        calculate_qualifying_loss(
            back_odds,
            lay_odds,
            stake,
            lay_stake,
            commission
        )
    )

    fta_profit = (
        calculate_fta_profit(
            stake,
            back_odds,
            lay_stake,
            commission
        )
    )

    expected_profit = (
        calculate_expected_profit(
            fta_profit,
            qualifying_loss,
            fta_pct
        )
    )

    ev_percent = (
        calculate_ev_percent(
            expected_profit,
            qualifying_loss
        )
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Lay Stake",
        f"£{lay_stake:.2f}"
    )

    c2.metric(
        "Liability",
        f"£{liability:.2f}"
    )

    c3.metric(
        "Qualifying Loss",
        f"£{qualifying_loss:.2f}"
    )

    c1.metric(
        "FTA Profit",
        f"£{fta_profit:.2f}"
    )

    c2.metric(
        "Expected Profit",
        f"£{expected_profit:.2f}"
    )

    c3.metric(
        "EV %",
        f"{ev_percent:.2f}%"
    )

# ==================================
# TRACKING
# ==================================

with tab_tracking:

    st.header(
        "📌 Tracked Bets"
    )

    bets = get_tracked_bets()

    if bets:

        columns = [

            "id",
            "match_name",
            "team",
            "league",
            "kickoff",

            "back_odds",
            "lay_odds",

            "stake",
            "commission",

            "lay_stake",
            "liability",

            "qualifying_loss",
            "outcome_fta",

            "fta_pct",
            "ev_pct",

            "expected_profit",
            "actual_profit",

            "status",
            "result",

            "model_version",

            "created_at",
            "settled_at"
        ]

        df = pd.DataFrame(
            bets,
            columns=columns
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.info(
            "No tracked bets found."
        )

# ==================================
# CALCULATOR
# ==================================

with tab_calc:

    st.header(
        "🧮 2UP Calculator"
    )

    col1, col2 = st.columns(2)

    with col1:

        back_odds = st.number_input(
            "Back Odds ",
            min_value=1.01,
            value=4.50
        )

        lay_odds = st.number_input(
            "Lay Odds ",
            min_value=1.01,
            value=4.75
        )

        stake = st.number_input(
            "Stake ",
            min_value=1.0,
            value=40.0
        )

        commission = st.number_input(
            "Commission ",
            min_value=0.0,
            value=2.0
        )

        fta_pct = st.number_input(
            "FTA Probability %",
            min_value=0.0,
            value=2.5
        )

    lay_stake = calculate_lay_stake(
        back_odds,
        lay_odds,
        stake,
        commission
    )

    liability = calculate_liability(
        lay_odds,
        lay_stake
    )

    qualifying_loss = (
        calculate_qualifying_loss(
            back_odds,
            lay_odds,
            stake,
            lay_stake,
            commission
        )
    )

    fta_profit = (
        calculate_fta_profit(
            stake,
            back_odds,
            lay_stake,
            commission
        )
    )

    expected_profit = (
        calculate_expected_profit(
            fta_profit,
            qualifying_loss,
            fta_pct
        )
    )

    ev_percent = (
        calculate_ev_percent(
            expected_profit,
            qualifying_loss
        )
    )

    with col2:

        st.metric(
            "Lay Stake",
            f"£{lay_stake:.2f}"
        )

        st.metric(
            "Liability",
            f"£{liability:.2f}"
        )

        st.metric(
            "Qualifying Loss",
            f"£{qualifying_loss:.2f}"
        )

        st.metric(
            "FTA Profit",
            f"£{fta_profit:.2f}"
        )

        st.metric(
            "Expected Profit",
            f"£{expected_profit:.2f}"
        )

        st.metric(
            "EV %",
            f"{ev_percent:.2f}%"
        )

# ==================================
# PERFORMANCE
# ==================================

with tab_perf:

    st.header(
        "📈 Performance"
    )

    total_bets, expected_profit, actual_profit = (
        get_performance_stats()
    )

    tracked_bets = (
        get_tracked_bets()
    )

    won_bets = 0
    lost_bets = 0

    total_staked = 0

    for row in tracked_bets:

        stake = row[7]

        profit = row[16]

        if profit is not None:

            total_staked += (
                stake or 0
            )

            if profit > 0:
                won_bets += 1

            elif profit < 0:
                lost_bets += 1

    roi = calculate_roi(
        actual_profit,
        total_staked
    )

    win_rate = calculate_win_rate(
        won_bets,
        lost_bets
    )

    p1, p2, p3 = st.columns(3)

    p1.metric(
        "Total Bets",
        total_bets
    )

    p2.metric(
        "Expected Profit",
        f"£{expected_profit:.2f}"
    )

    p3.metric(
        "Actual Profit",
        f"£{actual_profit:.2f}"
    )

    p1.metric(
        "ROI %",
        f"{roi:.2f}%"
    )

    p2.metric(
        "Win Rate %",
        f"{win_rate:.2f}%"
    )

    p3.metric(
        "Won / Lost",
        f"{won_bets}/{lost_bets}"
    )
