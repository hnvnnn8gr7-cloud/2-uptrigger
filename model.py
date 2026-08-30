import math


def calculate_hybrid_fta(
    back_odds,
    is_home=True
):

    implied_win_prob = 1 / back_odds

    home_bias = 1.10 if is_home else 0.90

    exp_goals = (
        implied_win_prob
        * 2.65
        * home_bias
    )

    p0 = math.exp(-exp_goals)

    p1 = (
        exp_goals
        * math.exp(-exp_goals)
    )

    p2plus = 1 - (p0 + p1)

    return round(
        max(
            0.80,
            min(
                p2plus *
                implied_win_prob *
                10,
                3.50
            )
        ),
        2
    )


def calculate_lay_stake(
    stake,
    back_odds,
    lay_odds,
    commission
):

    commission_rate = (
        commission / 100
    )

    lay_stake = (
        back_odds *
        stake
    ) / (
        lay_odds -
        commission_rate
    )

    return round(
        lay_stake,
        2
    )


def calculate_qualifying_loss(
    stake,
    back_odds,
    lay_odds,
    commission
):

    lay_stake = calculate_lay_stake(
        stake,
        back_odds,
        lay_odds,
        commission
    )

    back_loss = stake

    lay_profit = (
        lay_stake *
        (
            1 -
            (
                commission /
                100
            )
        )
    )

    return round(
        abs(
            back_loss -
            lay_profit
        ),
        2
    )


def calculate_turnaround_profit(
    stake,
    back_odds
):

    return round(
        stake *
        (
            back_odds - 1
        ),
        2
    )


def calculate_ev(
    back_odds,
    lay_odds,
    fta_pct,
    commission=2.0,
    stake=100
):

    qualifying_loss = (
        calculate_qualifying_loss(
            stake,
            back_odds,
            lay_odds,
            commission
        )
    )

    turnaround_profit = (
        calculate_turnaround_profit(
            stake,
            back_odds
        )
    )

    exchange_commission = (
        turnaround_profit *
        (
            commission /
            100
        )
    )

    expected_profit = (
        (
            turnaround_profit
            -
            exchange_commission
        )
        *
        (
            fta_pct / 100
        )
    ) - qualifying_loss

    ev = (
        100
        +
        (
            expected_profit
            /
            stake
        ) * 100
    )

    return round(
        ev,
        2
    )


def calculate_expected_profit(
    back_odds,
    lay_odds,
    fta_pct,
    stake,
    commission
):

    qualifying_loss = (
        calculate_qualifying_loss(
            stake,
            back_odds,
            lay_odds,
            commission
        )
    )

    turnaround_profit = (
        calculate_turnaround_profit(
            stake,
            back_odds
        )
    )

    exchange_commission = (
        turnaround_profit *
        (
            commission /
            100
        )
    )

    expected_profit = (
        (
            turnaround_profit
            -
            exchange_commission
        )
        *
        (
            fta_pct / 100
        )
    ) - qualifying_loss

    return round(
        expected_profit,
        2
    )


def calculate_ranking_score(
    ev_pct,
    fta_pct,
    xg_edge=0
):

    return round(
        (
            ev_pct * 0.50
        )
        +
        (
            fta_pct * 10 * 0.30
        )
        +
        (
            xg_edge * 10 * 0.20
        ),
        2
    )


def get_ev_color(
    ev
):

    if ev >= 115:
        return "#00c853"

    if ev >= 110:
        return "#2962ff"

    if ev >= 105:
        return "#00bfa5"

    if ev >= 100:
        return "#fdd835"

    return "#ef5350"
