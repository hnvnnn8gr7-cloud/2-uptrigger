import streamlit as st

# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(
    page_title="2UP Master V3",
    page_icon="⚽",
    layout="wide"
)

# ==================================
# APP HEADER
# ==================================

st.title("⚽ 2UP Master V3")

st.caption(
    "Machine Learning Powered 2UP Opportunity Discovery & Tracking Platform"
)

# ==================================
# NAVIGATION
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
        "Machine learning ranked opportunities will appear here."
    )

    st.markdown(
        """
        Future Metrics:

        - Match
        - Team
        - League
        - FTA %
        - EV %
        - Outcome QL
        - Outcome FTA
        - Expected Profit
        - Track Bet
        """
    )

# ==================================
# TRACKING
# ==================================

with tab_tracking:

    st.header(
        "📌 Tracking"
    )

    st.info(
        "Saved and tracked bets will appear here."
    )

    st.markdown(
        """
        Future Metrics:

        - Pending Bets
        - Won Bets
        - Lost Bets
        - Actual Profit
        - Expected Profit
        - Delete Bet
        """
    )

# ==================================
# CALCULATOR
# ==================================

with tab_calc:

    st.header(
        "🧮 Calculator"
    )

    st.info(
        "Standalone 2UP calculator."
    )

    st.markdown(
        """
        Future Inputs:

        - Back Odds
        - Lay Odds
        - Stake
        - Commission

        Future Outputs:

        - Lay Stake
        - Liability
        - Outcome QL
        - Outcome FTA
        - FTA %
        - EV %
        - Expected Profit
        """
    )

# ==================================
# PERFORMANCE
# ==================================

with tab_perf:

    st.header(
        "📈 Performance"
    )

    st.info(
        "Performance analytics will appear here."
    )

    st.markdown(
        """
        Future Metrics:

        - Total Bets
        - Won
        - Lost
        - Pending
        - Win Rate
        - ROI
        - Expected Profit
        - Actual Profit

        Future Charts:

        - Cumulative Profit
        - Expected vs Actual
        - ROI Over Time
        - Bank Growth
        """
    )
