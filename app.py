import os
import subprocess
import joblib
import pandas as pd
import streamlit as st

from datetime import datetime

from database import (
    create_tables,
    get_db
)

from model import (
    calculate_hybrid_fta,
    calculate_ev
)


create_tables()

st.set_page_config(
    page_title="2UP Master",
    page_icon="⚽",
    layout="wide"
)

MODEL_FILE = "fta_model.pkl"

st.title(
    "⚡ 2UP Master Finder"
)

# --------------------------
# MODEL STATUS
# --------------------------

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
        "No trained model found."
    )

# --------------------------
# RETRAIN BUTTON
# --------------------------

st.subheader(
    "Model Controls"
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

# --------------------------
# LOAD MODEL
# --------------------------

model = None

try:

    model = joblib.load(
        MODEL_FILE
    )

except:

    model = None

# --------------------------
# MODEL VERSION
# --------------------------

model_version = st.selectbox(
    "Prediction Method",
    [
        "ML Model",
        "Hybrid Model"
    ]
)

# --------------------------
# TEAM DATA
# --------------------------

conn = get_db()

teams = conn.execute(
    """
    SELECT team
    FROM team_stats
    ORDER BY team
    """
).fetchall()

team_list = [
    row[0]
    for row in teams
]

selected_team = st.selectbox(
    "Team",
    team_list
)

stats = conn.execute(
    """
    SELECT

        avg_xg,
        avg_xga,

        goals_last5,
        conceded_last5,

        turnaround_pct,

        two_up_trigger_rate,

        historical_turnaround_rate,

        historical_matches,

        historical_two_up,

        historical_comebacks

    FROM team_stats

    WHERE team = ?
    """,
    (
        selected_team,
    )
).fetchone()

conn.close()

# --------------------------
# USER INPUT
# --------------------------

col1, col2 = st.columns(2)

with col1:

    back_odds = st.number_input(
        "Back Odds",
        min_value=1.01,
        value=4.0
    )

with col2:

    lay_odds = st.number_input(
        "Lay Odds",
        min_value=1.01,
        value=4.2
    )

is_home = st.checkbox(
    "Home Team",
    value=True
)

# --------------------------
# TEAM STATS
# --------------------------

if stats:

    avg_xg = stats[0] or 0
    avg_xga = stats[1] or 0

    goals_last5 = stats[2] or 0
    conceded_last5 = stats[3] or 0

    turnaround_pct = stats[4] or 0

    trigger_rate = stats[5] or 0

    historical_turnaround_rate = (
        stats[6] or 0
    )

    historical_matches = (
        stats[7] or 0
    )

    historical_two_up = (
        stats[8] or 0
    )

    historical_comebacks = (
        stats[9] or 0
    )

else:

    avg_xg = 0
    avg_xga = 0

    goals_last5 = 0
    conceded_last5 = 0

    turnaround_pct = 0

    trigger_rate = 0

    historical_turnaround_rate = 0

    historical_matches = 0

    historical_two_up = 0

    historical_comebacks = 0

# --------------------------
# FTA CALCULATION
# --------------------------

if (
    model
    and
    model_version == "ML Model"
):

    features = pd.DataFrame(
        [
            [
                avg_xg,
                avg_xga,

                goals_last5,
                conceded_last5,

                turnaround_pct,

                trigger_rate,

                historical_turnaround_rate,

                int(is_home),

                45,

                2,

                back_odds,

                0,

                0,
                0,

                0,
                0
            ]
        ],
        columns=[
            "avg_xg",
            "avg_xga",

            "goals_last5",
            "conceded_last5",

            "turnaround_pct",

            "two_up_trigger_rate",

            "historical_turnaround_rate",

            "is_home",

            "lead_minute",

            "max_lead",

            "opening_back_odds",

            "odds_movement",

            "red_cards_for",
            "red_cards_against",

            "shots_for",
            "shots_against"
        ]
    )

    fta_pct = round(
        model.predict_proba(
            features
        )[0][1] * 100,
        2
    )

    source = "ML Model"

else:

    fta_pct = calculate_hybrid_fta(
        back_odds,
        is_home
    )

    source = "Hybrid Model"

ev_pct = calculate_ev(
    back_odds,
    lay_odds,
    fta_pct
)

# --------------------------
# OUTPUT
# --------------------------

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "FTA %",
        f"{fta_pct:.2f}%"
    )

with col2:

    st.metric(
        "EV %",
        f"{ev_pct:.2f}%"
    )

st.caption(
    f"Source: {source}"
)

st.markdown("---")

st.subheader(
    "Team Profile"
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Average xG",
        f"{avg_xg:.2f}"
    )

    st.metric(
        "Average xGA",
        f"{avg_xga:.2f}"
    )

with c2:

    st.metric(
        "Goals Last 5",
        goals_last5
    )

    st.metric(
        "Conceded Last 5",
        conceded_last5
    )

with c3:

    st.metric(
        "Recent Turnaround %",
        f"{turnaround_pct:.2f}"
    )

    st.metric(
        "Historical Turnaround %",
        f"{historical_turnaround_rate:.2f}"
    )

st.markdown("---")

st.subheader(
    "Historical 2UP Profile"
)

st.write(
    f"Historical Matches: {historical_matches}"
)

st.write(
    f"Historical 2UP Triggers: {historical_two_up}"
)

st.write(
    f"Historical Combacks: {historical_comebacks}"
)

st.write(
    f"2UP Trigger Rate: {trigger_rate:.2f}%"
)
