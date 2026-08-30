import joblib
import pandas as pd

from database import get_db
from xgboost import XGBClassifier


MODEL_FILE = "fta_model.pkl"


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
            f"Only {len(df)} rows found."
        )

        print(
            "Need at least 100 rows."
        )

        return

    features = [

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

    for col in features:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.fillna(0)

    X = df[features]

    y = pd.to_numeric(
        df["full_turnaround"],
        errors="coerce"
    ).fillna(0)

    if "sample_weight" in df.columns:

        weights = pd.to_numeric(
            df["sample_weight"],
            errors="coerce"
        ).fillna(1.0)

    else:

        weights = None

    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        eval_metric="logloss"
    )

    if weights is not None:

        model.fit(
            X,
            y,
            sample_weight=weights
        )

    else:

        model.fit(
            X,
            y
        )

    joblib.dump(
        model,
        MODEL_FILE
    )

from database import save_model_run

    save_model_run( 
    "ML_V1",
    len(df),
    "Historical + API model"
)

    
    print(
        f"Model trained on {len(df)} rows"
    )

    print(
        f"Saved {MODEL_FILE}"
    )

    print("\nTop Features:\n")

    importance = sorted(
        zip(
            features,
            model.feature_importances_
        ),
        key=lambda x: x[1],
        reverse=True
    )

    for feature, score in importance:

        print(
            f"{feature}: {score:.4f}"
        )


if __name__ == "__main__":
    train_model()
