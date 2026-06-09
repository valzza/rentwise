"""Download the UCI 'Apartment for Rent Classified' dataset to data/raw/apartments.csv.

This is REAL US rental-listing data (UCI ML Repository, id=555). The public download
is a .zip that contains two **.7z** archives (10K and 100K rows); the inner CSVs are
';'-delimited and latin-1 encoded. We use the 10K file by default (plenty for the
analysis and fast to process).

Two acquisition paths are attempted:
1. Direct zip download + 7z extraction (fast, ~1 min, deterministic).  [primary]
2. `ucimlrepo.fetch_ucirepo(id=555)` as a fallback.

Run from anywhere:  python src/download_data.py
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_CSV = RAW_DIR / "apartments.csv"

UCI_ID = 555
ZIP_URL = "https://archive.ics.uci.edu/static/public/555/apartment+for+rent+classified.zip"


def _save(df, source: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"[ok] Saved {len(df):,} rows x {df.shape[1]} cols from {source}")
    print(f"[ok] -> {OUT_CSV}")
    print(f"[ok] columns: {list(df.columns)}")


def via_zip() -> None:
    import tempfile

    import pandas as pd
    import py7zr

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / "_uci_source.zip"
    if cache.exists():
        print(f"[..] using cached zip: {cache}")
        blob = cache.read_bytes()
    else:
        print(f"[..] Downloading zip: {ZIP_URL} (this can take ~1 minute)")
        req = Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=180) as resp:
            blob = resp.read()
        cache.write_bytes(blob)
        print(f"[..] downloaded {len(blob):,} bytes")

    zf = zipfile.ZipFile(io.BytesIO(blob))
    members = zf.namelist()
    print(f"[..] zip members: {members}")
    # Prefer the 10K archive; fall back to whatever .7z is present.
    name7z = next((m for m in members if "10K" in m and m.lower().endswith(".7z")), None)
    if name7z is None:
        name7z = next(m for m in members if m.lower().endswith(".7z"))
    print(f"[..] extracting {name7z}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        inner = io.BytesIO(zf.read(name7z))
        with py7zr.SevenZipFile(inner, "r") as z:
            z.extractall(path=tmp)
        csv_path = next(p for p in tmp.rglob("*") if p.is_file())
        print(f"[..] inner file: {csv_path.name}")
        df = pd.read_csv(csv_path, sep=";", encoding="latin-1", low_memory=False)
    _save(df, f"zip:{name7z}:{csv_path.name}")


def via_ucimlrepo() -> None:
    import pandas as pd
    from ucimlrepo import fetch_ucirepo

    print(f"[..] Falling back to ucimlrepo.fetch_ucirepo(id={UCI_ID}) ...")
    ds = fetch_ucirepo(id=UCI_ID)
    frames = [f for f in (ds.data.features, ds.data.targets) if f is not None]
    df = pd.concat(frames, axis=1)
    _save(df, "ucimlrepo API")


def main() -> int:
    if OUT_CSV.exists():
        print(f"[skip] {OUT_CSV} already exists. Delete it to re-download.")
        return 0
    try:
        via_zip()
        return 0
    except Exception as exc:  # noqa: BLE001 - any failure -> fallback
        print(f"[warn] zip path failed: {exc!r}")
    try:
        via_ucimlrepo()
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[error] Could not download the dataset: {exc!r}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
