import joblib
import pandas as pd
import streamlit as st

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

st.title(
    "⚡ 2UP Master Finder"
)

MODEL_FILE = "fta_model.pkl"

model = None

try:

    model = joblib.load(
        MODEL_FILE
    )

except:

    model = None

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

        historical_turnaround_rate

    FROM team_stats

    WHERE team = ?
    """,
    (
        selected_team,
    )
).fetchone()

conn.close()

back_odds = st.number_input(
    "Back Odds",
    min_value=1.01,
    value=4.0
)

lay_odds = st.number_input(
    "Lay Odds",
    min_value=1.01,
    value=4.2
)

is_home = st.checkbox(
    "Home Team",
    value=True
)

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

else:

    avg_xg = 0
    avg_xga = 0

    goals_last5 = 0
    conceded_last5 = 0

    turnaround_pct = 0

    trigger_rate = 0

    historical_turnaround_rate = 0

if model:

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

    ml_probability = (
        model.predict_proba(
            features
        )[0][1]
        * 100
    )

    fta_pct = round(
        ml_probability,
        2
    )

    model_source = "ML Model"

else:

    fta_pct = calculate_hybrid_fta(
        back_odds,
        is_home
    )

    model_source = (
        "Fallback Hybrid Model"
    )

ev_pct = calculate_ev(
    back_odds,
    lay_odds,
    fta_pct
)

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

st.markdown("---")

st.subheader(
    "ML Features"
)

st.write(
    f"Model Source: {model_source}"
)

st.write(
    f"Average xG: {avg_xg:.2f}"
)

st.write(
    f"Average xGA: {avg_xga:.2f}"
)

st.write(
    f"Goals Last 5: {goals_last5}"
)

st.write(
    f"Conceded Last 5: {conceded_last5}"
)

st.write(
    f"Recent Turnaround %: {turnaround_pct:.2f}"
)

st.write(
    f"Historical 2UP Trigger Rate: {trigger_rate:.2f}"
)

st.write(
    f"Historical Turnaround Rate: {historical_turnaround_rate:.2f}"
)
