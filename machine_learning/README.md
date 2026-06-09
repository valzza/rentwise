# Rental Price-Tier Classification & Clustering

A machine-learning project on **real US rental-listing data** (the UCI *Apartment for
Rent Classified* dataset). Monthly rent is framed as a 3-class **price-tier**
classification problem (`Budget` / `Mid` / `Premium`), and the same listings are also
**clustered** and compared against those tiers.

This folder is **self-contained** — it has no dependency on the rest of the repository
and can be copied/moved anywhere and run on its own.

## What's inside

```
machine_learning/
├── requirements.txt          # Python dependencies
├── data/raw/                 # downloaded dataset (created by download_data.py)
├── src/
│   ├── download_data.py      # fetch + extract the UCI dataset -> data/raw/apartments.csv
│   ├── preprocessing.py      # cleaning, feature engineering, price-tier target, train/test split
│   ├── evaluation.py         # metrics, comparison table, confusion-matrix plots
│   └── clustering.py         # k selection, PCA visualisation, cluster-vs-tier agreement
├── notebooks/
│   └── 01_rental_ml.ipynb    # the full analysis (run this)
├── results/                  # figures + CSV tables produced by the notebook
├── report/REPORT.md          # the written report
└── build_notebook.py         # regenerates the notebook skeleton (optional)
```

## Setup

Requires **Python 3.10+** (developed and tested on 3.14).

```bash
# from inside the machine_learning/ folder
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
```

## Run

1. **Download the data** (≈10 MB zip, takes about a minute the first time):

   ```bash
   python src/download_data.py
   ```

   This writes `data/raw/apartments.csv`. It is idempotent — delete that file to
   re-download.

2. **Run the analysis notebook:**

   ```bash
   jupyter lab            # then open notebooks/01_rental_ml.ipynb and Run All
   ```

   or execute it headlessly:

   ```bash
   jupyter nbconvert --to notebook --execute --inplace notebooks/01_rental_ml.ipynb
   ```

   The notebook downloads the data automatically if it is missing, so step 1 is
   optional.

All figures and comparison tables are written to `results/`. The narrative write-up is
in `report/REPORT.md`.

## What the notebook covers

- **EDA & preprocessing** — cleaning, amenity counting, outlier trimming, one-hot +
  scaling pipeline, stratified 80/20 split.
- **Classification** — six models across four families: KNN (distance), Decision Tree
  & Random Forest (tree), Logistic Regression (linear), MLP (neural network), plus a
  Gradient Boosting model; benchmarked against a majority-class baseline.
- **Hyperparameter tuning** — `GridSearchCV` (5-fold) per model, with tested grids and
  chosen values logged to `results/hyperparameter_tuning.csv`.
- **Feature selection / reduction** — `SelectKBest` and `PCA` variants vs. the full set.
- **Neural-network architectures** — several depth/width/activation configurations
  compared.
- **Regression bridge** — a `GradientBoostingRegressor` on raw rent (the model the
  companion RentWise application productionises), reported with MAE / R².
- **Clustering** — KMeans (k swept 2–8, init experiments) plus Agglomerative
  clustering, visualised in PCA-2D and compared to the true tiers with ARI / NMI /
  homogeneity and a contingency table.

## Reproducibility

A fixed `random_state=42` is used throughout (splits, models, KMeans).
