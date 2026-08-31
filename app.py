import os
import uuid
import subprocess
import joblib

import pandas as pd
import streamlit as st

from datetime import datetime

from database import (
    create_tables,
    get_db,
    get_tracked_bets,
    save_tracked_bet,
    delete_tracked_bet,
    update_bet_result,
    get_performance_stats,
    get_model_runs
)

from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss
)

from performance import (
    calculate_roi
)

from model import (
    calculate_hybrid_fta,
    calculate_ev
)

# ----------------------------------
# INITIALISE
# ----------------------------------

create_tables()

st.set_page_config(
    page_title="2UP Master V2",
    page_icon="⚽",
    layout="wide"
)

MODEL_FILE = "fta_model.pkl"

st.title(
    "⚽ 2UP Master V2"
)

# ----------------------------------
# SIDEBAR
# ----------------------------------

st.sidebar.header(
    "Filters"
)

min_fta = st.sidebar.slider(
    "Minimum FTA %",
    min_value=0,
    max_value=100,
    value=0
)

max_fta = st.sidebar.slider(
    "Maximum FTA %",
    min_value=0,
    max_value=100,
    value=100
)

min_ev = st.sidebar.slider(
    "Minimum EV %",
    min_value=0,
    max_value=200,
    value=100
)

if st.sidebar.button(
    "Reset Filters"
):
    st.rerun()

# ----------------------------------
# MODEL STATUS
# ----------------------------------

if os.path.exists(MODEL_FILE):

    modified = datetime.fromtimestamp(
        os.path.getmtime(MODEL_FILE)
    )

    st.success(
        f"Model last trained: {modified}"
    )

else:

    st.warning(
        "No trained model found."
    )

# ----------------------------------
# CREATE TABS
# ----------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "⚡ Opportunities",
        "⭐ Best Bets",
        "📌 Tracked Bets",
        "📈 Performance",
        "🧪 Model Lab",
        "🤖 Model Controls"
    ]
)

# ==================================
# OPPORTUNITIES
# ==================================

with tab1:

    st.header(
        "⚡ Opportunities"
    )

    conn = get_db()

    odds_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM odds_history
        """
    ).fetchone()[0]

    conn.close()

    st.metric(
        "Stored Opportunities",
        odds_count
    )

    st.info(
        "Opportunities will populate automatically when odds_history contains live data."
    )

# ==================================
# BEST BETS
# ==================================

with tab2:

    st.header(
        "⭐ Best Bets"
    )

    st.info(
        "Best EV opportunities will appear here."
    )

# ==================================
# TRACKED BETS
# ==================================

with tab3:

    st.header(
        "📌 Tracked Bets"
    )

    st.subheader(
        "Add Manual Bet"
    )

    col1, col2 = st.columns(2)

    with col1:

        match_name = st.text_input(
            "Match Name"
        )

        team_name = st.text_input(
            "Team"
        )

        back_odds = st.number_input(
            "Back Odds",
            min_value=1.01,
            value=4.00,
            key="tb_back_odds"
        )

        stake = st.number_input(
            "Stake (£)",
            min_value=1.0,
            value=10.0,
            key="tb_stake"
        )

    with col2:

        lay_odds = st.number_input(
            "Lay Odds",
            min_value=1.01,
            value=4.20,
            key="tb_lay_odds"
        )

        commission = st.number_input(
            "Commission %",
            min_value=0.0,
            max_value=20.0,
            value=2.0
        )

        model_used = st.selectbox(
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

    qualifying_loss = (
        calculate_qualifying_loss(
            back_odds,
            lay_odds,
            stake,
            lay_stake,
            commission
        )
    )

    m1, m2, m3 = st.columns(3)

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
            "Qualifying Loss",
            f"£{qualifying_loss}"
        )

    if st.button(
        "⭐ Save Bet"
    ):

        save_tracked_bet(
            {
                "id": str(
                    uuid.uuid4()
                ),

                "match_name": match_name,

                "team": team_name,

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

                "expected_profit": 0,

                "actual_profit": 0,

                "result": "Pending",

                "model_version": model_used,

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

    bets = get_tracked_bets()

    if not bets:

        st.info(
            "No tracked bets yet."
        )

    else:

        for bet in bets:

            with st.expander(
                f"{bet[1]} | {bet[2]}"
            ):

                st.write(
                    f"Stake: £{bet[7]}"
                )

                st.write(
                    f"Lay Stake: £{bet[9]}"
                )

                st.write(
                    f"Liability: £{bet[10]}"
                )

                st.write(
                    f"Qualifying Loss: £{bet[11]}"
                )

                st.write(
                    f"Result: {bet[16]}"
                )

                a, b, c = st.columns(3)

                with a:

                    if st.button(
                        "✅ Won",
                        key=f"won_{bet[0]}"
                    ):

                        update_bet_result(
                            bet[0],
                            "Won",
                            abs(
                                float(
                                    bet[14]
                                )
                            )
                        )

                        st.rerun()

                with b:

                    if st.button(
                        "❌ Lost",
                        key=f"lost_{bet[0]}"
                    ):

                        update_bet_result(
                            bet[0],
                            "Lost",
                            -abs(
                                float(
                                    bet[11]
                                )
                            )
                        )

                        st.rerun()

                with c:

                    if st.button(
                        "🗑 Delete",
                        key=f"delete_{bet[0]}"
                    ):

                        delete_tracked_bet(
                            bet[0]
                        )

                        st.rerun()


# ==================================
# PERFORMANCE
# ==================================

with tab4:

    st.header(
        "📈 Performance Dashboard"
    )

    bets = get_tracked_bets()

    stats = get_performance_stats()

    total_bets = stats[0]

    expected_profit = round(
        stats[1] or 0,
        2
    )

    actual_profit = round(
        stats[2] or 0,
        2
    )

    roi = calculate_roi()

    won_count = 0
    lost_count = 0

    for bet in bets:

        result = bet[16]

        if result == "Won":
            won_count += 1

        elif result == "Lost":
            lost_count += 1

    settled_bets = (
        won_count +
        lost_count
    )

    if settled_bets > 0:

        win_rate = round(
            (
                won_count /
                settled_bets
            ) * 100,
            2
        )

    else:

        win_rate = 0

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:

        st.metric(
            "Total Bets",
            total_bets
        )

    with c2:

        st.metric(
            "Win Rate",
            f"{win_rate}%"
        )

    with c3:

        st.metric(
            "Expected Profit",
            f"£{expected_profit}"
        )

    with c4:

        st.metric(
            "Actual Profit",
            f"£{actual_profit}"
        )

    with c5:

        st.metric(
            "ROI",
            f"{roi}%"
        )

    st.markdown("---")

    pending_bets = (
        total_bets -
        settled_bets
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        st.metric(
            "Won",
            won_count
        )

    with p2:

        st.metric(
            "Lost",
            lost_count
        )

    with p3:

        st.metric(
            "Pending",
            pending_bets
        )

    st.markdown("---")

    if len(bets) > 0:

        running_actual = 0
        running_expected = 0

        actual_curve = []
        expected_curve = []

        for bet in reversed(
            bets
        ):

            running_expected += float(
                bet[14] or 0
            )

            running_actual += float(
                bet[15] or 0
            )

            expected_curve.append(
                running_expected
            )

            actual_curve.append(
                running_actual
            )

        chart_df = pd.DataFrame(
            {
                "Expected Profit":
                expected_curve,

                "Actual Profit":
                actual_curve
            }
        )

        st.subheader(
            "Expected vs Actual"
        )

        st.line_chart(
            chart_df
        )

    else:

        st.info(
            "No performance data yet."
        )

    st.markdown("---")

    st.subheader(
        "Current Summary"
    )

    if actual_profit > 0:

        st.success(
            f"Overall Profit: £{actual_profit}"
        )

    elif actual_profit < 0:

        st.error(
            f"Overall Loss: £{actual_profit}"
        )

    else:

        st.info(
            "Break Even"
        )

with tab5:

    st.header(
        "🧪 Model Lab"
    )

    model_runs = get_model_runs()

    if not model_runs:

        st.info(
            "No model runs recorded yet."
        )

    else:

        st.subheader(
            "Training History"
        )

        model_df = pd.DataFrame(
            model_runs,
            columns=[
                "ID",
                "Model",
                "Trained At",
                "Training Rows",
                "Notes"
            ]
        )

        st.dataframe(
            model_df,
            use_container_width=True
        )

        st.markdown("---")

        st.subheader(
            "Latest Run"
        )

        latest = model_runs[0]

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Model",
                latest[1]
            )

        with c2:

            st.metric(
                "Training Rows",
                latest[3]
            )

        with c3:

            st.metric(
                "Run ID",
                latest[0]
            )

        st.write(
            f"Training Date: {latest[2]}"
        )

        st.write(
            f"Notes: {latest[4]}"
        )

        st.markdown("---")

        available_models = sorted(
            list(
                set(
                    model_df["Model"]
                )
            )
        )

        st.subheader(
            "Model Comparison"
        )

        model_a = st.selectbox(
            "Model A",
            available_models,
            key="model_a"
        )

        model_b = st.selectbox(
            "Model B",
            available_models,
            key="model_b"
        )

        compare_col1, compare_col2 = st.columns(2)

        with compare_col1:

            st.success(
                f"Model A: {model_a}"
            )

        with compare_col2:

            st.info(
                f"Model B: {model_b}"
            )

        st.markdown("---")

        st.subheader(
            "Champion Model"
        )

        champion = st.selectbox(
            "Active Model",
            available_models,
            key="champion_model"
        )

        st.success(
            f"Champion Model: {champion}"
        )

        st.markdown("---")

        if os.path.exists(
            MODEL_FILE
        ):

            model_modified = datetime.fromtimestamp(
                os.path.getmtime(
                    MODEL_FILE
                )
            )

            st.info(
                f"Current model file updated: {model_modified}"
            )

            file_size = round(
                os.path.getsize(
                    MODEL_FILE
                ) / 1024,
                2
            )

            st.write(
                f"Model Size: {file_size} KB"
            )

        st.markdown("---")

        st.subheader(
            "Future Comparison Metrics"
        )

        st.write(
            "ROI comparison coming in V3."
        )

        st.write(
            "Win rate comparison coming in V3."
        )

        st.write(
            "Feature importance viewer coming in V3."
        )

        st.write(
            "Backtesting suite coming in V3."
        )

with tab6:

    st.header(
        "🤖 Model Controls"
    )

    st.subheader(
        "Model Management"
    )

    if st.button(
        "🔄 Retrain Model"
    ):

        with st.spinner(
            "Retraining model..."
        ):

            result = subprocess.run(
                [
                    "venv/bin/python",
                    "retrain_model.py"
                ],
                capture_output=True,
                text=True
            )

            if result.stdout:

                st.success(
                    "Training complete"
                )

                st.code(
                    result.stdout
                )

            if result.stderr:

                st.error(
                    result.stderr
                )

    st.markdown("---")

    st.subheader(
        "Model Diagnostics"
    )

    if os.path.exists(
        MODEL_FILE
    ):

        modified = datetime.fromtimestamp(
            os.path.getmtime(
                MODEL_FILE
            )
        )

        size_kb = round(
            os.path.getsize(
                MODEL_FILE
            ) / 1024,
            2
        )

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "Model Size",
                f"{size_kb} KB"
            )

        with c2:

            st.metric(
                "Last Updated",
                modified.strftime(
                    "%Y-%m-%d"
                )
            )

    else:

        st.error(
            "Model file not found."
        )

    st.markdown("---")

    st.subheader(
        "Team Profile Explorer"
    )

    conn = get_db()

    teams = conn.execute(
        """
        SELECT team
        FROM team_stats
        ORDER BY team
        """
    ).fetchall()

    if teams:

        team_list = [
            row[0]
            for row in teams
        ]

        selected_team = st.selectbox(
            "Select Team",
            team_list,
            key="team_explorer"
        )

        data = conn.execute(
            """
            SELECT

                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                two_up_trigger_rate,

                historical_turnaround_rate

            FROM team_stats

            WHERE team = ?
            """,
            (
                selected_team,
            )
        ).fetchone()

        if data:

            t1, t2, t3 = st.columns(3)

            with t1:

                st.metric(
                    "Avg xG",
                    round(
                        data[0] or 0,
                        2
                    )
                )

                st.metric(
                    "Avg xGA",
                    round(
                        data[1] or 0,
                        2
                    )
                )

            with t2:

                st.metric(
                    "Goals Last 5",
                    data[2] or 0
                )

                st.metric(
                    "Conceded Last 5",
                    data[3] or 0
                )

            with t3:

                st.metric(
                    "Turnaround %",
                    round(
                        data[4] or 0,
                        2
                    )
                )

                st.metric(
                    "2UP Trigger %",
                    round(
                        data[5] or 0,
                        2
                    )
                )

    conn.close()

    st.markdown("---")

    st.subheader(
        "Database Health"
    )

    conn = get_db()

    team_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM team_stats
        """
    ).fetchone()[0]

    training_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM training_data
        """
    ).fetchone()[0]

    odds_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM odds_history
        """
    ).fetchone()[0]

    result_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM match_results
        """
    ).fetchone()[0]

    conn.close()

    d1, d2, d3, d4 = st.columns(4)

    with d1:

        st.metric(
            "Teams",
            team_count
        )

    with d2:

        st.metric(
            "Training Rows",
            training_count
        )

    with d3:

        st.metric(
            "Odds Records",
            odds_count
        )

    with d4:

        st.metric(
            "Match Results",
            result_count
        )

    st.markdown("---")

    st.subheader(
        "System Status"
    )

    if odds_count == 0:

        st.warning(
            "Odds API data not currently available."
        )

    else:

        st.success(
            "Odds data available."
        )

    if training_count > 0:

        st.success(
            "Training dataset ready."
        )

    else:

        st.error(
            "Training dataset empty."
        )

