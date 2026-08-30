import os
import subprocess
import joblib
import streamlit as st

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

with tabsst.header(
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
        "📈 Performance"
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
