from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss,
    calculate_fta_profit,
)

from model import predict_fta


def calculate_expected_profit(
    fta_profit,
    qualifying_loss,
    fta_pct
):
    p = fta_pct / 100

    return (
        (fta_profit * p)
        -
        (
            abs(qualifying_loss)
            * (1 - p)
        )
    )


def calculate_ev_percent(
    expected_profit,
    qualifying_loss
):
    if qualifying_loss == 0:
        return 0

    return (
        expected_profit
        /
        abs(qualifying_loss)
    ) * 100


def rank_score(
    expected_profit,
    fta_pct
):
    return (
        expected_profit
        * (fta_pct / 100)
    )


def build_opportunity(
    fixture,
    stake=40,
    commission=2
):
    back_odds = fixture["back_odds"]
    lay_odds = fixture["lay_odds"]

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

    ql = calculate_qualifying_loss(
        stake,
        back_odds,
        lay_odds,
        lay_stake
    )

    fta_profit = calculate_fta_profit(
        stake,
        back_odds,
        lay_stake,
        commission
    )

    fta_pct = predict_fta(fixture)

    expected_profit = (
        calculate_expected_profit(
            fta_profit,
            ql,
            fta_pct
        )
    )

    ev_percent = (
        calculate_ev_percent(
            expected_profit,
            ql
        )
    )

    return {
        "match": fixture["match"],
        "league": fixture["league"],
        "team": fixture["team"],
        "back_odds": back_odds,
        "lay_odds": lay_odds,
        "fta_pct": round(
            fta_pct,
            2
        ),
        "ql": round(
            ql,
            2
        ),
        "fta_profit": round(
            fta_profit,
            2
        ),
        "expected_profit": round(
            expected_profit,
            2
        ),
        "ev_percent": round(
            ev_percent,
            2
        ),
        "ranking_score": rank_score(
            expected_profit,
            fta_pct
        )
    }


def rank_opportunities(
    fixtures
):
    opportunities = [
        build_opportunity(f)
        for f in fixtures
    ]

    return sorted(
        opportunities,
        key=lambda x: x[
            "ranking_score"
        ],
        reverse=True
    )
