from database import get_db

from calculations import (
    calculate_lay_stake,
    calculate_liability,
    calculate_qualifying_loss,
    calculate_fta_profit,
    calculate_expected_profit,
    calculate_ev_percent,
    calculate_ranking_score
)

from model import (
    predict_with_confidence,
    build_feature_vector
)


def estimate_lay_odds(
    back_odds
):
    """
    Estimate exchange lay odds when
    exchange data is unavailable.
    """

    if back_odds < 2:
        margin = 0.03

    elif back_odds < 5:
        margin = 0.05

    else:
        margin = 0.08

    return round(
        back_odds * (1 + margin),
        2
    )


def get_team_stats(
    team
):
    conn = get_db()

    row = conn.execute(
        """
        SELECT

            avg_xg,
            avg_xga,
            xg_edge,

            goals_last5,
            conceded_last5,

            turnaround_pct,

            historical_turnaround_rate,

            two_up_trigger_rate,

            league_turnaround_rate,

            opponent_turnaround_rate

        FROM team_stats

        WHERE team = ?
        """,
        (team,)
    ).fetchone()

    conn.close()

    if not row:
        return None

    return {
        "avg_xg": row[0],
        "avg_xga": row[1],
        "xg_edge": row[2],
        "goals_last5": row[3],
        "conceded_last5": row[4],
        "turnaround_pct": row[5],
        "historical_turnaround_rate": row[6],
        "two_up_trigger_rate": row[7],
        "league_turnaround_rate": row[8],
        "opponent_turnaround_rate": row[9]
    }


def build_opportunity(
    fixture,
    stake=40,
    commission=2
):
    team = fixture["team"]

    stats = get_team_stats(
        team
    )

    if not stats:
        return None

    back_odds = fixture[
        "back_odds"
    ]

    supplied_lay_odds = fixture.get(
        "lay_odds"
    )

    estimated_lay = False

    if supplied_lay_odds is None:

        lay_odds = estimate_lay_odds(
            back_odds
        )

        estimated_lay = True

    else:

        lay_odds = supplied_lay_odds

    feature_vector = build_feature_vector(
        team_stats=stats,

        is_home=fixture.get(
            "is_home",
            True
        ),

        opening_back_odds=
        back_odds,

        lead_minute=0,

        shots_for=0,
        shots_against=0,

        red_cards_for=0,
        red_cards_against=0
    )

    prediction = (
        predict_with_confidence(
            feature_vector
        )
    )

    fta_pct = prediction[
        "fta_pct"
    ]

    confidence = prediction[
        "confidence"
    ]

    lay_stake = (
        calculate_lay_stake(
            back_odds,
            lay_odds,
            stake,
            commission
        )
    )

    liability = (
        calculate_liability(
            lay_odds,
            lay_stake
        )
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

    ranking_score = (
        calculate_ranking_score(
            expected_profit,
            fta_pct
        )
    )

    return {

        "match":
            fixture.get(
                "match",
                ""
            ),

        "team":
            team,

        "league":
            fixture.get(
                "league",
                ""
            ),

        "bookmaker":
            fixture.get(
                "bookmaker",
                ""
            ),

        "back_odds":
            round(
                back_odds,
                2
            ),

        "lay_odds":
            round(
                lay_odds,
                2
            ),

        "estimated_lay":
            estimated_lay,

        "fta_pct":
            round(
                fta_pct,
                2
            ),

        "confidence":
            round(
                confidence,
                2
            ),

        "stake":
            stake,

        "commission":
            commission,

        "lay_stake":
            round(
                lay_stake,
                2
            ),

        "liability":
            round(
                liability,
                2
            ),

        "qualifying_loss":
            round(
                qualifying_loss,
                2
            ),

        "fta_profit":
            round(
                fta_profit,
                2
            ),

        "expected_profit":
            round(
                expected_profit,
                2
            ),

        "ev_percent":
            round(
                ev_percent,
                2
            ),

        "ranking_score":
            round(
                ranking_score,
                4
            )
    }


def rebuild_opportunity(
    opportunity,
    lay_odds,
    commission
):
    """
    Recalculate metrics when user
    changes lay odds or commission.
    """

    back_odds = opportunity[
        "back_odds"
    ]

    stake = opportunity.get(
        "stake",
        40
    )

    lay_stake = (
        calculate_lay_stake(
            back_odds,
            lay_odds,
            stake,
            commission
        )
    )

    liability = (
        calculate_liability(
            lay_odds,
            lay_stake
        )
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
            opportunity[
                "fta_pct"
            ]
        )
    )

    ev_percent = (
        calculate_ev_percent(
            expected_profit,
            qualifying_loss
        )
    )

    opportunity[
        "lay_odds"
    ] = round(
        lay_odds,
        2
    )

    opportunity[
        "commission"
    ] = commission

    opportunity[
        "lay_stake"
    ] = round(
        lay_stake,
        2
    )

    opportunity[
        "liability"
    ] = round(
        liability,
        2
    )

    opportunity[
        "qualifying_loss"
    ] = round(
        qualifying_loss,
        2
    )

    opportunity[
        "fta_profit"
    ] = round(
        fta_profit,
        2
    )

    opportunity[
        "expected_profit"
    ] = round(
        expected_profit,
        2
    )

    opportunity[
        "ev_percent"
    ] = round(
        ev_percent,
        2
    )

    opportunity[
        "estimated_lay"
    ] = False

    return opportunity


def rank_opportunities(
    fixtures
):
    opportunities = []

    for fixture in fixtures:

        opportunity = (
            build_opportunity(
                fixture
            )
        )

        if opportunity:
            opportunities.append(
                opportunity
            )

    opportunities.sort(
        key=lambda x:
        x["ranking_score"],
        reverse=True
    )

    return opportunities


def get_top_opportunities(
    fixtures,
    limit=20
):
    return rank_opportunities(
        fixtures
    )[:limit]
