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

    feature_vector = (
        build_feature_vector(
            team_stats=stats,

            is_home=fixture.get(
                "is_home",
                True
            ),

            opening_back_odds=
            fixture[
                "back_odds"
            ],

            lead_minute=0,

            shots_for=0,
            shots_against=0,

            red_cards_for=0,
            red_cards_against=0
        )
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

    back_odds = fixture[
        "back_odds"
    ]

    lay_odds = fixture[
        "lay_odds"
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
            fixture[
                "match"
            ],

        "team":
            team,

        "league":
            fixture[
                "league"
            ],

        "back_odds":
            back_odds,

        "lay_odds":
            lay_odds,

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

        "lay_stake":
            lay_stake,

        "liability":
            liability,

        "qualifying_loss":
            qualifying_loss,

        "fta_profit":
            fta_profit,

        "expected_profit":
            expected_profit,

        "ev_percent":
            ev_percent,

        "ranking_score":
            ranking_score
    }


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

    opportunities = sorted(
        opportunities,
        key=lambda x:
            x["ranking_score"],
        reverse=True
    )

    return opportunities


def get_top_opportunities(
    fixtures,
    limit=20
):

    ranked = (
        rank_opportunities(
            fixtures
        )
    )

    return ranked[:limit]
