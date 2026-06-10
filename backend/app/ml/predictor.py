import os
import numpy as np
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
MARGIN = 0.15  # ±15% for min/max range


class ModelPredictor:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"ML model not found at {MODEL_PATH}. Run: python -m app.ml.train")

        payload = joblib.load(MODEL_PATH)
        self.model = payload["model"]
        self.version: str = payload["version"]
        self.features: list = payload["features"]

    def predict(self, features: dict) -> dict:
        # Coerce missing/None feature values to 0 (e.g. optional neighborhood_id),
        # since the regressor rejects NaN.
        row = [[(0 if features.get(f) is None else features.get(f)) for f in self.features]]
        suggested = float(self.model.predict(row)[0])
        return {
            "suggested_price": round(suggested, 2),
            "min_price": round(suggested * (1 - MARGIN), 2),
            "max_price": round(suggested * (1 + MARGIN), 2),
            "model_version": self.version,
        }
