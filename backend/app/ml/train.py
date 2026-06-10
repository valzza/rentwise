"""
Train the RentWise price model on REAL US rental data.

Run once before starting the server:
    cd backend
    python -m app.ml.train

Trains a GradientBoostingRegressor on real listings from the UCI 'Apartment for
Rent Classified' dataset (loaded via app.ml.prepare_real_data) and writes
app/ml/model.pkl. No synthetic data is generated.

Notes on the real data:
  - prices are monthly rents in USD,
  - the legacy `size_m2` feature carries SQUARE FEET (US listings),
  - the dataset has no `floor` or `furnished` field, so those are not used /
    held constant; `city_id` matches the ids seeded by prepare_real_data.py.
"""
import os

import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.ml.prepare_real_data import FEATURES, get_training_frame

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
MODEL_VERSION = "3.0.0-real-us"
RANDOM_STATE = 42


def train():
    print("Loading REAL US rental data (UCI Apartment for Rent Classified)...")
    df = get_training_frame()
    print(f"  rows: {len(df):,}  cities: {df['city_id'].nunique()}  "
          f"price range: ${df['price'].min():,.0f}-${df['price'].max():,.0f}")

    # Fit on plain arrays (no feature names) so inference with a positional
    # feature list (see predictor.py) does not emit sklearn warnings.
    X, y = df[FEATURES].to_numpy(), df["price"].to_numpy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=RANDOM_STATE
    )

    model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.1,
        random_state=RANDOM_STATE,
    )
    print("Training GradientBoostingRegressor...")
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    print(f"MAE on test set: ${mean_absolute_error(y_test, pred):,.0f}")
    print(f"R^2 on test set: {r2_score(y_test, pred):.3f}")

    # Sanity-check a few real-shaped scenarios (city_id, neighborhood_id, sqft,
    # rooms, baths, furnished, pet, amenities).
    samples = {
        "1-bed 700 sqft (city 1)":  [1, 0, 700, 1, 1, 0, 0, 3],
        "2-bed 1000 sqft (city 1)": [1, 0, 1000, 2, 2, 0, 1, 5],
        "studio 450 sqft (city 2)": [2, 0, 450, 1, 1, 0, 0, 1],
    }
    print("\nSample predictions:")
    for label, row in samples.items():
        print(f"  {label}: ${model.predict([row])[0]:,.0f}/mo")

    joblib.dump({"model": model, "version": MODEL_VERSION, "features": FEATURES}, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    train()
