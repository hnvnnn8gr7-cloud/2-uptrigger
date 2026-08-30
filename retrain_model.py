import joblib
import pandas as pd

from database import get_db
from xgboost import XGBClassifier


def train_model():

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM training_data
        """,
        conn
    )

    conn.close()

    if len(df) < 100:

        print(
            "Need at least 100 rows"
        )

        return

    features = [

        "avg_xg",
        "avg_xga",

        "goals_last5",
        "conceded_last5",

        "turnaround_pct",

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

    X = df[features]

    y = df["full_turnaround"]

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        random_state=42
    )

    model.fit(
        X,
        y
    )

    joblib.dump(
        model,
        "fta_model.pkl"
    )

    print(
        "fta_model.pkl saved"
    )


if __name__ == "__main__":
    train_model()
