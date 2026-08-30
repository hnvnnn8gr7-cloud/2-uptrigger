import os
import subprocess
import joblib
import streamlit as st
import pandas as pd


from datetime import datetime

from database import (
    create_tables,
    get_db,
    get_tracked_bets,
    get_performance_stats,
    get_model_runs
)

from performance import (
    calculate_roi
)

from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss
)

from database import (
    save_tracked_bet,
    update_bet_result,
    delete_tracked_bet
)


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

# ===================================
# SIDEBAR
# ===================================

st.sidebar.header(
    "Filters"
)

min_fta = st.sidebar.slider(
    "Minimum FTA %",
    0,
    100,
    0
)

min_ev = st.sidebar.slider(
    "Minimum EV %",
    0,
    200,
    100
)

if st.sidebar.button(
    "Reset Filters"
):

    st.rerun()

# ===================================
# MODEL STATUS
# ===================================

if os.path.exists(
    MODEL_FILE
):

    modified = datetime.fromtimestamp(
        os.path.getmtime(
            MODEL_FILE
        )
    )

    st.success(
        f"Model last trained: {modified}"
    )

else:

    st.warning(
        "No trained model found"
    )

# ===================================
# TABS
# ===================================

tabs = st.tabs(
    [
        "⚡ Opportunities",
        "⭐ Best Bets",
        "📌 Tracked Bets",
        "📈 Performance",
        "🧪 Model Lab",
        "🤖 Model Controls"
    ]
)

# ===================================
# OPPORTUNITIES
# ===================================

with tabs
python
st.header(
        "⚡ Opportunities"
    )


    st.info(
        "Will populate automatically when odds_history contains data."
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

# ===================================
# BEST BETS
# ===================================

with tabsst.header(
        "⭐ Best Bets"
    )


    st.info(
        "Best EV opportunities will appear here."
    )

# ===================================
# TRACKED BETS
# ===================================

with tabsst.header(
        "📌 Tracked Bets"
    )


    bets = get_tracked_bets()

    if not bets:

        st.info(
            "No tracked bets yet."
        )

    else:

        for bet in bets:

            st.write(bet)

# ===================================
# PERFORMANCE
# ===================================

with tabsst.header(
        "📈 Performance Dashboard"
    )


    stats = get_performance_stats()

    total_bets = stats[0]

    expected_profit = round(
        stats[1],
        2
    )

    actual_profit = round(
        stats[2],
        2
    )

    roi = calculate_roi()

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Total Bets",
            total_bets
        )

    with c2:

        st.metric(
            "Expected Profit",
            f"£{expected_profit}"
        )

    with c3:

        st.metric(
            "Actual Profit",
            f"£{actual_profit}"
        )

    with c4:

        st.metric(
            "ROI %",
            f"{roi}%"
        )

# ===================================
# MODEL LAB
# ===================================

with tabsst.header(
        "🧪 Model Lab"
    )


    model_runs = get_model_runs()

    if not model_runs:

        st.info(
            "No model runs recorded."
        )

    else:

        for run in model_runs:

            st.write(run)

# ===================================
# MODEL CONTROLS
# ===================================

with tabsst.header(
        "🤖 Model Controls"
    )


    if st.button(
        "🔄 Retrain Model"
    ):

        with st.spinner(
            "Training..."
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
                    "Training Complete"
                )

                st.code(
                    result.stdout
                )

            if result.stderr:

                st.error(
                    result.stderr
                )

    st.markdown("---")

    conn = get_db()

    teams = conn.execute(
        """
        SELECT team
        FROM team_stats
        ORDER BY team
        """
    ).fetchall()

    conn.close()

    if teams:

        team_list = [
            row[0]
            for row in teams
        ]

        selected_team = st.selectbox(
            "Team Profile",
            team_list
        )

        conn = get_db()

        team_data = conn.execute(
            """
            SELECT
                avg_xg,
                avg_xga,
                turnaround_pct,
                two_up_trigger_rate,
                historical_turnaround_rate
            FROM team_stats
            WHERE team = ?
            """,
            (selected_team,)
        ).fetchone()

        conn.close()

        if team_data:

            st.write(
                f"Average xG: {team_data[0]}"
            )

            st.write(
                f"Average xGA: {team_data[1]}"
            )

            st.write(
                f"Turnaround %: {team_data[2]}"
            )

            st.write(
                f"2UP Trigger Rate: {team_data[3]}"
            )

            st.write(
                f"Historical Turnaround Rate: {team_data[4]}"
            )

with tabs```

section with this:

```python
with tabsst.header(
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

        team = st.text_input(
            "Team"
        )

        back_odds = st.number_input(
            "Back Odds",
            min_value=1.01,
            value=4.0,
            key="track_back_odds"
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
            value=4.2,
            key="track_lay_odds"
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

    qualifying_loss = calculate_qualifying_loss(
        back_odds,
        lay_odds,
        stake,
        lay_stake,
        commission
    )

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Lay Stake",
            f"£{lay_stake}"
        )

    with c2:

        st.metric(
            "Liability",
            f"£{liability}"
        )

    with c3:

        st.metric(
            "Qualifying Loss",
            f"£{qualifying_loss}"
        )

    if st.button(
        "⭐ Save Bet"
    ):

        import uuid

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

    bets = get_tracked_bets()

    st.subheader(
        "Tracked Bets"
    )

    if not bets:

        st.info(
            "No tracked bets saved."
        )

    else:

        for bet in bets:

            with st.expander(
                f"{bet[1]} | {bet[2]}"
            ):

                st.write(
                    f"Back Odds: {bet[5]}"
                )

                st.write(
                    f"Lay Odds: {bet[6]}"
                )

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

                col_a, col_b, col_c = st.columns(
                    3
                )

                with col_a:

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

                with col_b:

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

                with col_c:

                    if st.button(
                        "🗑 Delete",
                        key=f"delete_{bet[0]}"
                    ):

                        delete_tracked_bet(
                            bet[0]
                        )

                        st.rerun()

with tabs```

with the following:

```python
with tabsst.header(
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

    if bets:

        dates = []
        cumulative_expected = []
        cumulative_actual = []

        running_expected = 0
        running_actual = 0

        for bet in reversed(bets):

            expected = float(
                bet[14] or 0
            )

            actual = float(
                bet[15] or 0
            )

            running_expected += expected
            running_actual += actual

            dates.append(
                bet[18]
            )

            cumulative_expected.append(
                running_expected
            )

            cumulative_actual.append(
                running_actual
            )

        chart_df = pd.DataFrame(
            {
                "Expected Profit":
                cumulative_expected,

                "Actual Profit":
                cumulative_actual
            }
        )

        st.subheader(
            "Expected vs Actual Profit"
        )

        st.line_chart(
            chart_df
        )

    else:

        st.info(
            "No settled bets available."
        )

    st.markdown("---")

    st.subheader(
        "Results Breakdown"
    )

    b1, b2, b3 = st.columns(3)

    with b1:

        st.metric(
            "Won",
            won_count
        )

    with b2:

        st.metric(
            "Lost",
            lost_count
        )

    with b3:

        st.metric(
            "Pending",
            total_bets -
            settled_bets
        )

with tabs```

with:

```python
with tabsst.header(
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

        latest_models = (
            model_df["Model"]
            .unique()
            .tolist()
        )

        if latest_models:

            model_a = st.selectbox(
                "Model A",
                latest_models,
                key="model_a"
            )

            model_b = st.selectbox(
                "Model B",
                latest_models,
                key="model_b"
            )

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Model A",
                    model_a
                )

            with col2:

                st.metric(
                    "Model B",
                    model_b
                )

        st.markdown("---")

        champion_model = st.selectbox(
            "Champion Model",
            latest_models,
            key="champion"
        )

        st.success(
            f"Current Champion: {champion_model}"
        )

        st.markdown("---")

        st.subheader(
            "Model Statistics"
        )

        latest_run = model_runs[0]

        st.write(
            f"Model: {latest_run[1]}"
        )

        st.write(
            f"Trained: {latest_run[2]}"
        )

        st.write(
            f"Training Rows: {latest_run[3]}"
        )

        st.write(
            f"Notes: {latest_run[4]}"
        )

        st.markdown("---")

        if os.path.exists(
            "fta_model.pkl"
        ):

            modified = datetime.fromtimestamp(
                os.path.getmtime(
                    "fta_model.pkl"
                )
            )

            st.info(
                f"Latest model file updated: {modified}"
            )

