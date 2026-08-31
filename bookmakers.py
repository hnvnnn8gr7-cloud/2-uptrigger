"""
2UP Master V3

Approved bookmakers list.

Only bookmakers in this file are allowed
to appear in Opportunities.

Bookmakers can be enabled/disabled without
changing application logic.
"""

TWO_UP_BOOKMAKERS = {

    "bet365": {
        "display_name": "Bet365",
        "enabled": True,
        "two_up": True
    },

    "paddypower": {
        "display_name": "Paddy Power",
        "enabled": True,
        "two_up": True
    },

    "skybet": {
        "display_name": "Sky Bet",
        "enabled": True,
        "two_up": True
    },

    "williamhill": {
        "display_name": "William Hill",
        "enabled": True,
        "two_up": True
    },

    "10bet": {
        "display_name": "10Bet",
        "enabled": True,
        "two_up": True
    },

    "barone": {
        "display_name": "Bar One Racing",
        "enabled": True,
        "two_up": True
    },

    "betfair_sb_uk": {
        "display_name": "Betfair Sportsbook",
        "enabled": False,
        "two_up": False
    }
}


def is_allowed_bookmaker(
    bookmaker_key
):
    """
    Returns True if bookmaker
    is approved and enabled.
    """

    bookmaker_key = (
        bookmaker_key
        .strip()
        .lower()
    )

    bookmaker = (
        TWO_UP_BOOKMAKERS.get(
            bookmaker_key
        )
    )

    if not bookmaker:
        return False

    return bookmaker[
        "enabled"
    ]


def get_display_name(
    bookmaker_key
):
    """
    Converts API bookmaker
    key to display name.
    """

    bookmaker_key = (
        bookmaker_key
        .strip()
        .lower()
    )

    bookmaker = (
        TWO_UP_BOOKMAKERS.get(
            bookmaker_key
        )
    )

    if bookmaker:

        return bookmaker[
            "display_name"
        ]

    return bookmaker_key


def get_allowed_bookmakers():
    """
    Returns all enabled bookmakers.
    """

    return [

        key

        for key, value
        in TWO_UP_BOOKMAKERS.items()

        if value["enabled"]

    ]


def get_two_up_bookmakers():
    """
    Returns only bookmakers
    offering 2UP.
    """

    return [

        key

        for key, value
        in TWO_UP_BOOKMAKERS.items()

        if (
            value["enabled"]
            and
            value["two_up"]
        )

    ]


if __name__ == "__main__":

    print(
        "Enabled bookmakers:"
    )

    for bookmaker in (
        get_allowed_bookmakers()
    ):

        print(
            bookmaker
        )
