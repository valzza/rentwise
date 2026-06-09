"""Loading, cleaning, feature engineering and train/test splitting for the
UCI 'Apartment for Rent Classified' dataset.

The task is framed as PRICE-TIER CLASSIFICATION: monthly rent is binned into three
tiers (Budget / Mid / Premium) by tertiles, giving a 3-class target that the
clustering step (k=3) can later be compared against.

All paths are resolved relative to this file so the folder is portable.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "apartments.csv"

RANDOM_STATE = 42
TIER_LABELS = ["Budget", "Mid", "Premium"]

# Engineered feature columns used by the models.
NUMERIC_FEATURES = ["square_feet", "bedrooms", "bathrooms", "amenities_count"]
CATEGORICAL_FEATURES = ["state", "is_pet_friendly", "has_photo_flag"]


def load_raw(csv_path: Path | str = RAW_CSV) -> pd.DataFrame:
    """Read the raw CSV (already normalised to comma-separated by download_data.py)."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run `python src/download_data.py` first."
        )
    return pd.read_csv(csv_path, low_memory=False)


def _coerce_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw rows and engineer the modelling features + the price target.

    Robust to column-name casing and to the price living in `price` or `price_display`.
    """
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    # --- price (target source) -------------------------------------------------
    price_col = "price" if "price" in df.columns else "price_display"
    df["price"] = _coerce_numeric(df[price_col].astype(str).str.replace(r"[^0-9.]", "", regex=True))

    # --- core numeric features -------------------------------------------------
    for col in ["bedrooms", "bathrooms", "square_feet"]:
        df[col] = _coerce_numeric(df.get(col))

    # --- amenities -> count ----------------------------------------------------
    if "amenities" in df.columns:
        df["amenities_count"] = (
            df["amenities"].fillna("").astype(str)
            .apply(lambda x: 0 if x.strip() in ("", "nan", "null") else len(x.split(",")))
        )
    else:
        df["amenities_count"] = 0

    # --- pets ------------------------------------------------------------------
    if "pets_allowed" in df.columns:
        pets = df["pets_allowed"].fillna("").astype(str).str.lower()
        df["is_pet_friendly"] = (~pets.isin(["", "none", "no", "nan", "null"])).astype(int)
    else:
        df["is_pet_friendly"] = 0

    # --- has_photo -> binary flag (a listing-quality signal) -------------------
    if "has_photo" in df.columns:
        photo = df["has_photo"].fillna("").astype(str).str.lower()
        df["has_photo_flag"] = (photo.isin(["thumbnail", "yes", "1", "true"])).astype(int)
    else:
        df["has_photo_flag"] = 0

    # --- state -----------------------------------------------------------------
    if "state" in df.columns:
        df["state"] = df["state"].fillna("UNK").astype(str).str.strip().str.upper()
    else:
        df["state"] = "UNK"

    # --- drop unusable rows ----------------------------------------------------
    df = df.dropna(subset=["price", "square_feet", "bedrooms", "bathrooms"])
    df = df[(df["price"] > 0) & (df["square_feet"] > 0)]

    # --- outlier trimming (monthly rents; drop the extreme tails) --------------
    lo, hi = df["price"].quantile([0.01, 0.99])
    df = df[(df["price"] >= lo) & (df["price"] <= hi)]
    sqf_hi = df["square_feet"].quantile(0.99)
    df = df[df["square_feet"] <= sqf_hi]
    df = df[(df["bedrooms"] <= 8) & (df["bathrooms"] <= 6)]

    # Collapse rare states into 'OTHER' so one-hot stays compact and stable.
    top_states = df["state"].value_counts().head(20).index
    df["state"] = np.where(df["state"].isin(top_states), df["state"], "OTHER")

    # --- target: price tier via tertiles ---------------------------------------
    df["price_tier"] = pd.qcut(df["price"], q=3, labels=TIER_LABELS)

    keep = NUMERIC_FEATURES + CATEGORICAL_FEATURES + ["price", "price_tier"]
    return df[keep].reset_index(drop=True)


def build_preprocessor() -> ColumnTransformer:
    """ColumnTransformer: scale numerics, one-hot encode categoricals."""
    numeric = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric, NUMERIC_FEATURES),
            ("cat", categorical, CATEGORICAL_FEATURES),
        ]
    )


def make_splits(df: pd.DataFrame, test_size: float = 0.2):
    """Stratified train/test split on the price tier. Returns X_train, X_test, y_train, y_test."""
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df["price_tier"].astype(str).copy()
    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=RANDOM_STATE
    )


def feature_matrix(df: pd.DataFrame):
    """Return (X, y) without splitting (used by clustering / feature-selection studies)."""
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df["price_tier"].astype(str).copy()
    return X, y
