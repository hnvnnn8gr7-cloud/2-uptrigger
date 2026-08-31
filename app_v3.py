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
        "Connect odds_collector.py to display live ranked opportunities."
    )

    st.write(
        "Future Columns:"
    )

    st.dataframe(
        pd.DataFrame(
            columns=[
                "Match",
                "Team",
                "League",
                "Back Odds",
                "Lay Odds",
                "FTA %",
                "Confidence",
                "Expected Profit",
                "EV %"
            ]
        ),
        use_container_width=True
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
            "No tracked bets yet."
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
            "Back Odds",
            min_value=1.01,
            value=4.60
        )

        lay_odds = st.number_input(
            "Lay Odds",
            min_value=1.01,
            value=5.00
        )

        stake = st.number_input(
            "Stake (£)",
            min_value=1.0,
            value=40.0
        )

        commission = st.number_input(
            "Commission %",
            min_value=0.0,
            value=2.0
        )

        fta_pct = st.number_input(
            "FTA %",
            min_value=0.0,
            value=2.53
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
            f"£{lay_stake}"
        )

        st.metric(
            "Liability",
            f"£{liability}"
        )

        st.metric(
            "Qualifying Loss",
            f"£{qualifying_loss}"
        )

        st.metric(
            "FTA Profit",
            f"£{fta_profit}"
        )

        st.metric(
            "Expected Profit",
            f"£{expected_profit}"
        )

        st.metric(
            "EV %",
            f"{ev_percent}%"
        )

# ==================================
# PERFORMANCE
# ==================================

with tab_perf:

    st.header(
        "📈 Performance"
    )

    total_bets, expected_profit_total, actual_profit_total = (
        get_performance_stats()
    )

    tracked_bets = get_tracked_bets()

    won_bets = 0
    lost_bets = 0

    total_staked = 0

    for row in tracked_bets:

        actual_profit = row[16]

        stake = row[7]

        if actual_profit is not None:

            total_staked += (
                stake or 0
            )

            if actual_profit > 0:
                won_bets += 1

            elif actual_profit < 0:
                lost_bets += 1

    roi = calculate_roi(
        actual_profit_total,
        total_staked
    )

    win_rate = calculate_win_rate(
        won_bets,
        lost_bets
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Bets",
        total_bets
    )

    c2.metric(
        "Expected Profit",
        f"£{round(expected_profit_total, 2)}"
    )

    c3.metric(
        "Actual Profit",
        f"£{round(actual_profit_total, 2)}"
    )

    c1.metric(
        "ROI %",
        roi
    )

    c2.metric(
        "Win Rate %",
        win_rate
    )

    c3.metric(
        "Won/Lost",
        f"{won_bets}/{lost_bets}"
    )
