import streamlit as st
import uuid

from datetime import datetime

from database import (
    get_tracked_bets,
    save_tracked_bet,
    delete_tracked_bet,
    update_bet_result
)

from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss,
    calculate_fta_profit
)


BET_COLUMNS = [
    "id",
    "match_name",
    "team",
    "league",
    "kickoff",

    "back_odds",
    "lay_odds",

    "stake",

    "lay_stake",
    "qualifying_loss",

    "fta_pct",
    "ev_pct",

    "expected_profit",
    "actual_profit",

    "result",
    "created_at",

    "commission",
    "liability",

    "model_version"
]



st.set_page_config(
    page_title="2UP Master V3",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ 2UP Master V3")

# ==================================
# TABS
# ==================================

tab_opps, tab_best, tab_bets, tab_perf, tab_models, tab_controls = st.tabs(
    [
        "⚡ Opportunities",
        "⭐ Best Bets",
        "📌 Bets",
        "📈 Performance",
        "🧪 Models",
        "🤖 Controls"
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
        "Live opportunities will appear here."
    )

# ==================================
# BEST BETS
# ==================================

with tab_best:

    st.header(
        "⭐ Best Bets"
    )

    st.info(
        "Highest EV opportunities will appear here."
    )

# ==================================
# BETS
# ==================================

with tab_bets:

    st.header("📌 Bets")

    st.subheader("New Bet")

    col1, col2 = st.columns(2)

    with col1:

        match_name = st.text_input(
            "Match Name"
        )

        team = st.text_input(
            "Team"
        )

        back_odds = st.number_input(
            "Back Odds",
            min_value=1.01,
            value=4.0
        )

        stake = st.number_input(
            "Stake (£)",
            min_value=1.0,
            value=10.0
        )

    with col2:

        lay_odds = st.number_input(
            "Lay Odds",
            min_value=1.01,
            value=4.2
        )

        commission = st.number_input(
            "Commission %",
            min_value=0.0,
            value=2.0
        )

        model_version = st.selectbox(
            "Model",
            [
                "ML_V1",
                "Hybrid"
            ]
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

    qualifying_loss = calculate_qualifying_loss(
        back_odds,
        lay_odds,
        stake,
        lay_stake,
        commission
    )

    fta_profit = calculate_fta_profit(
    stake,
    back_odds,
    lay_stake,
    commission
)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Lay Stake",
            f"£{lay_stake}"
        )

    with m2:
        st.metric(
            "Liability",
            f"£{liability}"
        )

    with m3:
        st.metric(
            "Outcome QL",
            f"£{qualifying_loss}"
        )

    with m4:
        st.metric(
            "FTA Profit",
            f"£{fta_profit}"
        )

    if st.button(
        "💾 Save Bet"
    ):

        save_tracked_bet(
            {
                "id": str(
                    uuid.uuid4()
                ),

                "match_name": match_name,
                "team": team,
                "league": "",
                "kickoff": "",

                "back_odds": back_odds,
                "lay_odds": lay_odds,

                "stake": stake,
                "commission": commission,

                "lay_stake": lay_stake,
                "liability": liability,

                "qualifying_loss": qualifying_loss,

                "fta_pct": 0,
                "ev_pct": 0,

                "expected_profit": fta_profit,
                "actual_profit": 0,

                "result": "Pending",

                "model_version": model_version,

                "created_at": datetime.now().isoformat()
            }
        )

        st.success(
            "Bet Saved"
        )

        st.rerun()

    st.markdown("---")

    st.subheader(
        "Saved Bets"
    )

    rows = get_tracked_bets()

    if not rows:

        st.info(
            "No bets saved."
        )

    else:

        for row in rows:

            bet = dict(
                zip(
                    BET_COLUMNS,
                    row
                )
            )

            with st.expander(
                f"{bet['match_name']} | {bet['team']}"
            ):

                st.json(bet)

                
                st.write(
                    f"Back Odds: {bet['back_odds']}"
                )

                st.write(
                    f"Lay Odds: {bet['lay_odds']}"
                )

                st.write(
                    f"Stake: £{bet['stake']}"
                )

                st.write(
                    f"Lay Stake: £{bet['lay_stake']}"
                )

                st.write(
                    f"Liability: £{bet['liability']}"
                )

                st.write(
                    f"Outcome QL: £{bet['qualifying_loss']}"
                )

                st.write(
                    f"FTA Profit: £{bet['expected_profit']}"
                )

                st.write(
                    f"Result: {bet['result']}"
                )

                a, b, c = st.columns(3)

                with a:

                    if st.button(
                        "✅ Won",
                        key=f"won_{bet['id']}"
                    ):

                        update_bet_result(
                            bet["id"],
                            "Won",
                            bet["expected_profit"]
                        )

                        st.rerun()

                with b:

                    if st.button(
                        "❌ Lost",
                        key=f"lost_{bet['id']}"
                    ):

                        update_bet_result(
                            bet["id"],
                            "Lost",
                            bet["qualifying_loss"]
                        )

                        st.rerun()

                with c:

                    if st.button(
                        "🗑 Delete",
                        key=f"delete_{bet['id']}"
                    ):

                        delete_tracked_bet(
                            bet["id"]
                        )

                        st.rerun()


# ==================================
# PERFORMANCE
# ==================================

with tab_perf:

    st.header(
        "📈 Performance"
    )

    st.info(
        "ROI and profit analytics coming next."
    )

# ==================================
# MODELS
# ==================================

with tab_models:

    st.header(
        "🧪 Models"
    )

    st.info(
        "Model history and comparisons coming next."
    )

# ==================================
# CONTROLS
# ==================================

with tab_controls:

    st.header(
        "🤖 Controls"
    )

    st.info(
        "Retraining and diagnostics coming next."
    )
