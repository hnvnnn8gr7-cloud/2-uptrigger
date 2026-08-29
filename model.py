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
    p1 = exp_goals * math.exp(-exp_goals)

    p2plus = 1 - (p0 + p1)

    return round(
        max(
            0.80,
            min(
                p2plus * implied_win_prob * 10,
                3.50
            )
        ),
        2
    )


def calculate_ev(
    back_odds,
    lay_odds,
    fta_pct,
    stake=100
):

    qualifying_loss = abs(
        stake -
        ((back_odds * stake) / lay_odds)
    )

    turnaround_profit = (
        stake *
        (back_odds - 1)
    )

    expected_profit = (
        turnaround_profit
        * (fta_pct / 100)
    ) - qualifying_loss

    return round(
        100 +
        ((expected_profit / stake) * 100),
        1
    )


def get_ev_color(ev):

    if ev >= 108:
        return "#00c853"

    if ev >= 104:
        return "#2962ff"

    if ev >= 100:
        return "#00bfa5"

    return "#9e9e9e"
