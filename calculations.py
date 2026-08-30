def calculate_lay_stake(
    back_odds,
    lay_odds,
    stake,
    commission
):

    return round(
        (
            back_odds * stake
        ) /
        (
            lay_odds -
            commission / 100
        ),
        2
    )


def calculate_liability(
    lay_odds,
    lay_stake
):

    return round(
        (
            lay_odds - 1
        ) * lay_stake,
        2
    )


def calculate_qualifying_loss(
    back_odds,
    lay_odds,
    stake,
    lay_stake,
    commission
):

    back_profit = (
        stake *
        (
            back_odds - 1
        )
    ) - (
        (lay_odds - 1)
        * lay_stake
    )

    lay_profit = (
        lay_stake *
        (
            1 -
            commission / 100
        )
    ) - stake

    return round(
        min(
            back_profit,
            lay_profit
        ),
        2
    )
