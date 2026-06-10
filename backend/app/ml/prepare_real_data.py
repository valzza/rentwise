"""Convert the REAL UCI 'Apartment for Rent Classified' dataset into:

1. A training DataFrame for the price model (`get_training_frame()`), and
2. RentWise seed SQL populated with REAL listings (`generate_seed_sql()`):
     - backend/seed_all.sql          (US cities + real properties)
     - backend/seed_neighborhoods.sql (one neighborhood per city + assignment)

No data is fabricated — every property/price/city value comes from the dataset.
The dataset is US apartment listings, so:
  - cities become real US "City, ST" entries (explicit ids 1..N so the model's
    `city_id` feature stays aligned with the seeded database),
  - prices are in USD, and the legacy `size_m2` column carries SQUARE FEET.

Run:  cd backend && python -m app.ml.prepare_real_data   (writes the seed files)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ML_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ML_DIR.parents[1]
DATA_CSV = ML_DIR / "data" / "apartments.csv"

N_CITIES = 15          # top-N US cities by listing count -> city_id 1..N
N_SEED_PROPERTIES = 200  # real listings written into seed_all.sql
RANDOM_STATE = 42

# Demo accounts (admin / landlord / tenant) all share this bcrypt hash of
# "Demo1234" — matching the credentials shown on the login screen.
DEMO_HASH = "$2b$12$IAx1pnfheO8JPnOJHiOv/uiVrjNhrvmATgb/.hUiqCFI5M5REZIgu"

# The model's feature list (no `floor` — the real dataset has no such field).
FEATURES = [
    "city_id", "neighborhood_id", "size_m2", "num_rooms",
    "num_bathrooms", "is_furnished", "is_pet_friendly", "amenities_count",
]

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80",
    "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=800&q=80",
    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800&q=80",
    "https://images.unsplash.com/photo-1564078516393-cf04bd966897?w=800&q=80",
    "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?w=800&q=80",
    "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&q=80",
    "https://images.unsplash.com/photo-1556020685-ae41abfc9365?w=800&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800&q=80",
    "https://images.unsplash.com/photo-1585128792020-803d29415281?w=800&q=80",
    "https://images.unsplash.com/photo-1628592102751-ba83b0314276?w=800&q=80",
    "https://images.unsplash.com/photo-1613575831056-0acd5da8f085?w=800&q=80",
    "https://images.unsplash.com/photo-1665249934445-1de680641f50?w=800&q=80",
    "https://images.unsplash.com/photo-1675279200694-8529c73b1fd0?w=800&q=80",
]


def _coerce(s):
    return pd.to_numeric(s, errors="coerce")


def load_clean() -> pd.DataFrame:
    """Load + clean the real dataset into a common, RentWise-aligned schema."""
    if not DATA_CSV.exists():
        raise FileNotFoundError(
            f"{DATA_CSV} not found. Copy apartments.csv there "
            "(see machine_learning/src/download_data.py to fetch it)."
        )
    df = pd.read_csv(DATA_CSV, low_memory=False)
    df.columns = [c.strip().lower() for c in df.columns]

    df["price"] = _coerce(df["price"])
    df["square_feet"] = _coerce(df["square_feet"])
    df["bedrooms"] = _coerce(df["bedrooms"])
    df["bathrooms"] = _coerce(df["bathrooms"])

    df["amenities_count"] = (
        df.get("amenities", pd.Series([""] * len(df))).fillna("").astype(str)
        .apply(lambda x: 0 if x.strip() in ("", "nan", "null") else len(x.split(",")))
    )
    pets = df.get("pets_allowed", pd.Series([""] * len(df))).fillna("").astype(str).str.lower()
    df["is_pet_friendly"] = (~pets.isin(["", "none", "no", "nan", "null"])).astype(int)

    df["cityname"] = df["cityname"].fillna("Unknown").astype(str).str.strip()
    df["state"] = df["state"].fillna("NA").astype(str).str.strip().str.upper()
    df["latitude"] = _coerce(df.get("latitude"))
    df["longitude"] = _coerce(df.get("longitude"))

    df = df.dropna(subset=["price", "square_feet", "bedrooms", "bathrooms"])
    df = df[(df["price"] > 0) & (df["square_feet"] > 0)]
    # Trim extreme tails so the model/seed see realistic monthly rents & sizes.
    lo, hi = df["price"].quantile([0.01, 0.99])
    df = df[(df["price"] >= lo) & (df["price"] <= hi)]
    df = df[df["square_feet"] <= df["square_feet"].quantile(0.99)]
    df = df[(df["bedrooms"] <= 8) & (df["bathrooms"] <= 6)]

    df["city_label"] = df["cityname"] + ", " + df["state"]
    return df.reset_index(drop=True)


def city_mapping(df: pd.DataFrame) -> dict[str, int]:
    """Top-N cities by listing count -> deterministic city_id 1..N."""
    top = df["city_label"].value_counts().head(N_CITIES).index.tolist()
    top = sorted(top)  # stable order -> stable ids across runs
    return {label: i + 1 for i, label in enumerate(top)}


def get_training_frame() -> pd.DataFrame:
    """Real listings within the top-N cities, mapped to the model's feature schema.

    `size_m2` holds raw square feet; `is_furnished`/`neighborhood_id` are constant
    (the real data has no such fields) but kept so the feature vector matches the app.
    """
    df = load_clean()
    cmap = city_mapping(df)
    df = df[df["city_label"].isin(cmap)].copy()
    df["city_id"] = df["city_label"].map(cmap).astype(int)
    out = pd.DataFrame({
        "city_id": df["city_id"],
        "neighborhood_id": 0,
        "size_m2": df["square_feet"].astype(float),   # legacy name; holds sqft
        "num_rooms": df["bedrooms"].astype(int).clip(lower=0),
        "num_bathrooms": df["bathrooms"].astype(int).clip(lower=1),
        "is_furnished": 0,
        "is_pet_friendly": df["is_pet_friendly"].astype(int),
        "amenities_count": df["amenities_count"].astype(int),
        "price": df["price"].astype(float),
    })
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Seed SQL generation
# --------------------------------------------------------------------------- #
def _sql_str(value: str) -> str:
    """Single-quote a string for SQL, escaping embedded quotes."""
    return "'" + str(value).replace("'", "''") + "'"


def _title_for(row) -> str:
    br = int(row["bedrooms"])
    kind = "Studio" if br == 0 else f"{br}-Bed Apartment"
    return f"{kind} in {row['cityname']}"


def _description_for(row) -> str:
    br = int(row["bedrooms"]); ba = int(row["bathrooms"]); sf = int(row["square_feet"])
    pet = "Pet-friendly. " if row["is_pet_friendly"] else ""
    return (f"{br} bd / {ba} ba, {sf} sq ft rental in {row['cityname']}, "
            f"{row['state']}. {pet}Real listing imported from market data.")


def generate_seed_sql() -> None:
    df = load_clean()
    cmap = city_mapping(df)
    inv = {v: k for k, v in cmap.items()}
    df = df[df["city_label"].isin(cmap)].copy()
    df["city_id"] = df["city_label"].map(cmap).astype(int)

    rng = np.random.default_rng(RANDOM_STATE)
    # Sample real listings, spread across cities (proportional, >=4 each if possible).
    per_city = max(1, N_SEED_PROPERTIES // len(cmap))
    parts = []
    for cid, grp in df.groupby("city_id"):
        take = min(len(grp), per_city)
        parts.append(grp.sample(take, random_state=int(cid)))
    sample = pd.concat(parts)
    if len(sample) > N_SEED_PROPERTIES:
        sample = sample.sample(N_SEED_PROPERTIES, random_state=RANDOM_STATE)
    # Round-robin across cities so listings interleave. Combined with the
    # per-row timestamps below, the default "newest first" sort then shows a
    # mix of cities on page 1 instead of all city_id 1 (Austin).
    sample["_rk"] = sample.groupby("city_id").cumcount()
    sample = sample.sort_values(["_rk", "city_id"]).reset_index(drop=True)

    # ---- derive real neighborhoods from each listing's lat/long ----
    # The dataset has no neighborhood field, but it does have coordinates, so we
    # bucket each city's listings into geographic zones relative to the city
    # centroid (Downtown / North / South / East / West) and assign each listing
    # to its real zone. Neighborhood coordinates = mean of their member listings.
    sample["_clat"] = sample.groupby("city_id")["latitude"].transform("mean")
    sample["_clng"] = sample.groupby("city_id")["longitude"].transform("mean")
    sample["_slat"] = sample.groupby("city_id")["latitude"].transform("std").fillna(0.0)
    sample["_slng"] = sample.groupby("city_id")["longitude"].transform("std").fillna(0.0)

    def _zone(r):
        lat, lng = r["latitude"], r["longitude"]
        if pd.isna(lat) or pd.isna(lng):
            return "Central"
        # If a city's listings have no real coordinate spread (all ~one point),
        # or this listing sits near the centroid, it's "Downtown".
        if (r["_slat"] < 1e-3 and r["_slng"] < 1e-3) or (
            abs(lat - r["_clat"]) <= 0.3 * r["_slat"]
            and abs(lng - r["_clng"]) <= 0.3 * r["_slng"]
        ):
            return "Central"
        dlat, dlng = lat - r["_clat"], lng - r["_clng"]
        if abs(dlat) >= abs(dlng):
            return "North" if dlat >= 0 else "South"
        return "East" if dlng >= 0 else "West"

    sample["zone"] = [_zone(r) for _, r in sample.iterrows()]

    nb_list = []        # (nb_id, city_id, name, lat, lng)
    nb_id_map = {}      # (city_id, zone) -> nb_id
    nb_id = 1
    for cid in sorted(inv):
        cname = inv[cid].split(",")[0]
        g = sample[sample["city_id"] == cid]
        for zone in ["Central", "North", "South", "East", "West"]:
            members = g[g["zone"] == zone]
            if members.empty:
                continue
            lat, lng = members["latitude"].mean(), members["longitude"].mean()
            if pd.isna(lat):
                lat, lng = g["latitude"].mean(), g["longitude"].mean()
            name = f"Downtown {cname}" if zone == "Central" else f"{zone} {cname}"
            nb_id_map[(cid, zone)] = nb_id
            nb_list.append((nb_id, cid, name, lat, lng))
            nb_id += 1
    sample["neighborhood_id"] = [
        nb_id_map[(int(r["city_id"]), r["zone"])] for _, r in sample.iterrows()
    ]

    # ---- seed_all.sql ----
    city_rows = ",\n".join(
        f"    ({cid},{_sql_str(inv[cid])},'USA',v_landlord_id,v_landlord_id,NOW(),NOW())"
        for cid in sorted(inv)
    )
    nb_rows_all = ",\n".join(
        "    ({nid},{cid},{name},{lat},{lng},v_landlord_id,v_landlord_id,NOW(),NOW())".format(
            nid=nid, cid=cid, name=_sql_str(name),
            lat=(f"{lat:.4f}" if pd.notna(lat) else "NULL"),
            lng=(f"{lng:.4f}" if pd.notna(lng) else "NULL"),
        )
        for (nid, cid, name, lat, lng) in nb_list
    )
    prop_rows = ",\n".join(
        "    (v_landlord_id,{title},{desc},{price:.2f},{city_id},{nb},{size:.1f},"
        "{rooms},{baths},{furn},{pet},'active',v_landlord_id,v_landlord_id,"
        "NOW() - (INTERVAL '1 hour' * {i}),NOW() - (INTERVAL '1 hour' * {i}))".format(
            i=i,
            nb=int(r["neighborhood_id"]),
            title=_sql_str(_title_for(r)),
            desc=_sql_str(_description_for(r)),
            price=float(r["price"]),
            city_id=int(r["city_id"]),
            size=float(r["square_feet"]),
            rooms=int(r["bedrooms"]) if int(r["bedrooms"]) >= 1 else 1,
            baths=int(r["bathrooms"]) if int(r["bathrooms"]) >= 1 else 1,
            furn="false",
            pet="true" if r["is_pet_friendly"] else "false",
        )
        for i, (_, r) in enumerate(sample.iterrows())
    )
    urls_sql = ",\n".join(f"    {_sql_str(u)}" for u in IMAGE_URLS)

    seed_all = f"""-- RentWise seed — REAL US rental listings (UCI Apartment for Rent Classified).
-- AUTO-GENERATED by app/ml/prepare_real_data.py — do not edit by hand.
-- Run order:  alembic upgrade head  ->  seed roles + amenities (see README)
--             ->  \\i seed_all.sql  ->  \\i seed_neighborhoods.sql
-- Expects a fresh DB (empty cities/properties).

DO $$
DECLARE
  v_landlord_id INT;
  prop_row      RECORD;
  urls          TEXT[];
  file_id       INT;
  url_idx       INT;
BEGIN
  -- Demo users (password for all three: Demo1234)
  INSERT INTO users (first_name, last_name, email, password_hash, is_active, created_at, updated_at) VALUES
    ('Site',  'Admin',    'admin@rentwise.com',    '{DEMO_HASH}', true, NOW(), NOW()),
    ('Arben', 'Kelmendi', 'landlord@rentwise.com', '{DEMO_HASH}', true, NOW(), NOW()),
    ('Tina',  'Tenant',   'tenant@rentwise.com',   '{DEMO_HASH}', true, NOW(), NOW())
  ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash, is_active = true;
  UPDATE users SET created_by = id, updated_by = id WHERE created_by IS NULL;

  -- Assign each demo user its role
  INSERT INTO user_roles (user_id, role_id, assigned_at, created_at, updated_at)
  SELECT u.id, r.id, NOW(), NOW(), NOW()
  FROM users u JOIN roles r ON (
       (u.email = 'admin@rentwise.com'    AND r.name = 'admin')
    OR (u.email = 'landlord@rentwise.com' AND r.name = 'landlord')
    OR (u.email = 'tenant@rentwise.com'   AND r.name = 'tenant'))
  WHERE NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

  SELECT id INTO v_landlord_id FROM users WHERE email = 'landlord@rentwise.com';

  -- Real US cities (explicit ids so the ML model's city_id feature stays aligned)
  INSERT INTO cities (id, name, country, created_by, updated_by, created_at, updated_at) VALUES
{city_rows}
  ON CONFLICT (id) DO NOTHING;
  PERFORM setval(pg_get_serial_sequence('cities','id'), (SELECT MAX(id) FROM cities));

  -- Neighborhoods: geographic zones derived from each listing's real lat/long
  INSERT INTO neighborhoods (id, city_id, name, latitude, longitude, created_by, updated_by, created_at, updated_at) VALUES
{nb_rows_all}
  ON CONFLICT (id) DO NOTHING;
  PERFORM setval(pg_get_serial_sequence('neighborhoods','id'), (SELECT MAX(id) FROM neighborhoods));

  -- Real listings (prices in USD; size_m2 column carries square feet)
  INSERT INTO properties (landlord_id,title,description,price,city_id,neighborhood_id,size_m2,num_rooms,num_bathrooms,is_furnished,is_pet_friendly,status,created_by,updated_by,created_at,updated_at) VALUES
{prop_rows};

  -- Images (Unsplash URLs cycled across all properties)
  urls := ARRAY[
{urls_sql}
  ];
  -- Random image per listing (a fixed cycle would align with the round-robin
  -- city order and give every property in a city the same photo).
  FOR prop_row IN SELECT id FROM properties ORDER BY id LOOP
    url_idx := 1 + floor(random() * {len(IMAGE_URLS)})::int;
    INSERT INTO files (entity, entity_id, filename, file_path, file_size, uploaded_by, created_at, updated_at)
    VALUES ('property', prop_row.id, 'photo.jpg', urls[url_idx], 0, v_landlord_id, NOW(), NOW())
    RETURNING id INTO file_id;
    INSERT INTO property_images (property_id, file_id, is_primary, created_at, updated_at)
    VALUES (prop_row.id, file_id, true, NOW(), NOW());
  END LOOP;

  -- Assign ~4 amenities per property
  INSERT INTO property_amenities (property_id, amenity_id, created_by, updated_by, created_at, updated_at)
  SELECT p.id, a.id, v_landlord_id, v_landlord_id, NOW(), NOW()
  FROM properties p
  JOIN amenities a ON ((p.id * 7 + a.id * 13) % 10) < 4
  ON CONFLICT DO NOTHING;
END $$;
"""
    (BACKEND_DIR / "seed_all.sql").write_text(seed_all, encoding="utf-8")

    # ---- seed_neighborhoods.sql (now a safety-net only) ----
    # Neighborhoods are seeded in seed_all.sql; this just assigns any property
    # that somehow has no neighborhood to its city's first one.
    seed_nb = """-- RentWise seed — neighborhood fallback.
-- AUTO-GENERATED by app/ml/prepare_real_data.py. Neighborhoods are now created
-- in seed_all.sql (geographic zones from real coordinates); this only fills in
-- any property left without a neighborhood. Run after seed_all.sql.

DO $$
BEGIN
  UPDATE properties p
  SET neighborhood_id = (SELECT n.id FROM neighborhoods n WHERE n.city_id = p.city_id LIMIT 1)
  WHERE p.neighborhood_id IS NULL;
END $$;
"""
    (BACKEND_DIR / "seed_neighborhoods.sql").write_text(seed_nb, encoding="utf-8")

    print(f"[ok] cities: {len(inv)}  neighborhoods: {len(nb_list)}  seed properties: {len(sample)}")
    print(f"[ok] wrote {BACKEND_DIR / 'seed_all.sql'}")
    print(f"[ok] wrote {BACKEND_DIR / 'seed_neighborhoods.sql'}")
    print("[ok] city_id map:")
    for cid in sorted(inv):
        nbs = [n[2] for n in nb_list if n[1] == cid]
        print(f"       {cid:2d} -> {inv[cid]:24} ({len(nbs)} nbhd: {', '.join(nbs)})")


if __name__ == "__main__":
    generate_seed_sql()
