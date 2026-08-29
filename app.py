import streamlit as st
from database import create_tables
from model import (
    calculate_hybrid_fta,
    calculate_ev,
    get_ev_color
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

back_odds = st.number_input(
    "Back Odds",
    1.01,
    value=4.0
)

lay_odds = st.number_input(
    "Lay Odds",
    1.01,
    value=4.2
)

fta_pct = calculate_hybrid_fta(
    back_odds
)

ev_pct = calculate_ev(
    back_odds,
    lay_odds,
    fta_pct
)

st.metric(
    "FTA %",
    f"{fta_pct}%"
)

st.metric(
    "EV %",
    f"{ev_pct}%"
)
