"""Builder for notebooks/01_rental_ml.ipynb.

Generates the analysis notebook programmatically with nbformat so the committed
.ipynb is always valid. Re-run this script to regenerate the notebook skeleton:
    python build_notebook.py
(The executed notebook with outputs is produced separately via `jupyter nbconvert --execute`.)
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "01_rental_ml.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


md(r"""
# Rental Price-Tier Classification & Clustering

**Dataset:** UCI *Apartment for Rent Classified* — real US rental listings.

**Problem.** Each listing's monthly rent is binned into three **price tiers**
(`Budget` / `Mid` / `Premium`) by tertiles. We then:

1. Train, tune and compare **six classifiers** spanning four families
   (distance-based, tree-based, linear, neural network) plus a gradient-boosting
   bridge to the RentWise app and a majority-class baseline.
2. Run a **feature-selection / dimensionality-reduction** study.
3. Experiment with **multiple neural-network architectures**.
4. Train a **regression bridge** (the model RentWise productionises) on raw rent.
5. **Cluster** the listings (labels removed) and compare clusters to the true tiers.

All metrics, tables and figures are written to `../results/`.
""")

code(r"""
import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Make the portable src/ helpers importable regardless of CWD.
SRC = Path.cwd().parent / "src" if (Path.cwd().name == "notebooks") else Path.cwd() / "src"
sys.path.insert(0, str(SRC.resolve()))

import preprocessing as prep
import evaluation as ev
import clustering as cl

RESULTS = (SRC.parent / "results")
RESULTS.mkdir(exist_ok=True)
print("src:", SRC.resolve())
print("results:", RESULTS.resolve())
""")

md("## 1. Load & explore the data")

code(r"""
# Download on first run (no-op if the CSV already exists).
import download_data
download_data.main()

raw = prep.load_raw()
print("raw shape:", raw.shape)
raw.head()
""")

code(r"""
print("Columns:", list(raw.columns))
raw.describe(include="all").T.head(25)
""")

md("## 2. Cleaning, feature engineering & price tiers")

code(r"""
df = prep.clean(raw)
print("clean shape:", df.shape)
print("\nFeatures used:")
print("  numeric    :", prep.NUMERIC_FEATURES)
print("  categorical:", prep.CATEGORICAL_FEATURES)
print("\nPrice-tier counts:")
print(df["price_tier"].value_counts())
df.head()
""")

code(r"""
# EDA: rent distribution + tier boundaries
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(df["price"], bins=50, ax=axes[0], color="steelblue")
axes[0].set(title="Monthly rent distribution (USD)", xlabel="rent")
sns.boxplot(data=df, x="price_tier", y="price", order=prep.TIER_LABELS, ax=axes[1])
axes[1].set(title="Rent by price tier", xlabel="tier", ylabel="rent")
fig.tight_layout()
fig.savefig(RESULTS / "eda_price.png", dpi=120, bbox_inches="tight")
plt.show()
""")

code(r"""
# Feature correlations (numeric)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(df[prep.NUMERIC_FEATURES + ["price"]].corr(), annot=True, fmt=".2f",
            cmap="coolwarm", ax=ax)
ax.set_title("Numeric feature correlations")
fig.tight_layout()
fig.savefig(RESULTS / "eda_corr.png", dpi=120, bbox_inches="tight")
plt.show()
""")

md("## 3. Train/test split & preprocessing pipeline")

code(r"""
X_train, X_test, y_train, y_test = prep.make_splits(df)
labels = prep.TIER_LABELS
print("train:", X_train.shape, " test:", X_test.shape)
print("class balance (train):")
print(y_train.value_counts(normalize=True).round(3))
""")

md("""
## 4. Classifiers — four families + baseline

| Model | Family |
|---|---|
| DummyClassifier | majority-class baseline |
| KNeighborsClassifier | distance-based |
| DecisionTree / RandomForest | tree-based |
| LogisticRegression | linear |
| MLPClassifier | **neural network** |
| GradientBoostingClassifier | boosting (bridge to RentWise) |
""")

code(r"""
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

def make_pipe(estimator):
    return Pipeline([("prep", prep.build_preprocessor()), ("clf", estimator)])

models = {
    "Baseline (majority)":  DummyClassifier(strategy="most_frequent"),
    "KNN":                  KNeighborsClassifier(n_neighbors=15),
    "DecisionTree":         DecisionTreeClassifier(max_depth=8, random_state=RANDOM_STATE),
    "RandomForest":         RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
    "LogisticRegression":   LogisticRegression(max_iter=1000),
    "MLP (neural net)":     MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=400, random_state=RANDOM_STATE),
    "GradientBoosting":     GradientBoostingClassifier(random_state=RANDOM_STATE),
}

rows, fitted = [], {}
for name, est in models.items():
    pipe = make_pipe(est).fit(X_train, y_train)
    pred = pipe.predict(X_test)
    fitted[name] = pipe
    rows.append(ev.score_model(name, y_test, pred))

baseline_table = ev.comparison_table(rows, save=False)
baseline_table.round(4)
""")

code(r"""
# Confusion matrices for the baseline and the two strongest default models
ev.plot_confusion(y_test, fitted["RandomForest"].predict(X_test), labels,
                  "RandomForest (default)", "cm_randomforest.png")
ev.plot_confusion(y_test, fitted["MLP (neural net)"].predict(X_test), labels,
                  "MLP (default)", "cm_mlp.png")
print(ev.text_report(y_test, fitted["RandomForest"].predict(X_test)))
""")

md("""
## 5. Hyperparameter tuning (GridSearchCV, 5-fold)

For each classifier we search a small, sensible grid and keep the best estimator.
Tested grids and chosen values are printed below and saved to `results/`.
""")

code(r"""
from sklearn.model_selection import GridSearchCV

grids = {
    "KNN": {
        "clf__n_neighbors": [5, 15, 25, 35],
        "clf__weights": ["uniform", "distance"],
    },
    "DecisionTree": {
        "clf__max_depth": [5, 8, 12, None],
        "clf__min_samples_leaf": [1, 5, 20],
    },
    "RandomForest": {
        "clf__n_estimators": [200, 400],
        "clf__max_depth": [None, 12, 20],
    },
    "LogisticRegression": {
        "clf__C": [0.1, 1.0, 10.0],
    },
    "GradientBoosting": {
        "clf__n_estimators": [100, 200],
        "clf__max_depth": [2, 3],
        "clf__learning_rate": [0.05, 0.1],
    },
}

tuned_rows, tuned_best = [], {}
tuning_log = []
for name, grid in grids.items():
    gs = GridSearchCV(make_pipe(models[name]), grid, cv=5, scoring="f1_macro", n_jobs=-1)
    gs.fit(X_train, y_train)
    tuned_best[name] = gs.best_estimator_
    pred = gs.best_estimator_.predict(X_test)
    tuned_rows.append(ev.score_model(name + " (tuned)", y_test, pred))
    tuning_log.append({"model": name, "tested": grid, "chosen": gs.best_params_,
                       "cv_f1_macro": round(gs.best_score_, 4)})
    print(f"{name:20s} best={gs.best_params_}  cv_f1={gs.best_score_:.4f}")

pd.DataFrame(tuning_log).to_csv(RESULTS / "hyperparameter_tuning.csv", index=False)
""")

md("## 6. Neural-network architecture experiments")

code(r"""
# Vary depth/width and activation; the preprocessing pipeline is shared.
architectures = [
    {"hidden_layer_sizes": (64,),         "activation": "relu"},
    {"hidden_layer_sizes": (128, 64),     "activation": "relu"},
    {"hidden_layer_sizes": (128, 64, 32), "activation": "relu"},
    {"hidden_layer_sizes": (128, 64),     "activation": "tanh"},
]

nn_rows = []
best_mlp, best_f1 = None, -1
for arch in architectures:
    mlp = MLPClassifier(max_iter=500, random_state=RANDOM_STATE, alpha=1e-4, **arch)
    pipe = make_pipe(mlp).fit(X_train, y_train)
    pred = pipe.predict(X_test)
    r = ev.score_model(f"MLP {arch['hidden_layer_sizes']} {arch['activation']}", y_test, pred)
    nn_rows.append(r)
    if r["f1_macro"] > best_f1:
        best_f1, best_mlp = r["f1_macro"], pipe

nn_table = pd.DataFrame(nn_rows)
nn_table.to_csv(RESULTS / "nn_architectures.csv", index=False)
nn_table.round(4)
""")

md("## 7. Feature selection / dimensionality reduction")

code(r"""
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.decomposition import PCA

def eval_variant(name, extra_steps):
    pipe = Pipeline([("prep", prep.build_preprocessor()), *extra_steps,
                     ("clf", RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1))])
    pipe.fit(X_train, y_train)
    return ev.score_model(name, y_test, pipe.predict(X_test))

fs_rows = [
    eval_variant("All features", []),
    eval_variant("SelectKBest(k=6)", [("select", SelectKBest(f_classif, k=6))]),
    eval_variant("SelectKBest(k=10)", [("select", SelectKBest(f_classif, k=10))]),
    eval_variant("PCA(5 comps)", [("pca", PCA(n_components=5, random_state=RANDOM_STATE))]),
    eval_variant("PCA(10 comps)", [("pca", PCA(n_components=10, random_state=RANDOM_STATE))]),
]
fs_table = pd.DataFrame(fs_rows)
fs_table.to_csv(RESULTS / "feature_selection.csv", index=False)
fs_table.round(4)
""")

md("## 8. Regression bridge to RentWise")

code(r"""
# RentWise productionises a GradientBoostingRegressor on raw rent. We train the
# same model here on the real data and report MAE / R^2 as the explicit link.
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

reg_df = df.copy()
Xr = reg_df[prep.NUMERIC_FEATURES + prep.CATEGORICAL_FEATURES]
yr = reg_df["price"]
from sklearn.model_selection import train_test_split
Xr_tr, Xr_te, yr_tr, yr_te = train_test_split(Xr, yr, test_size=0.2, random_state=RANDOM_STATE)

reg = Pipeline([("prep", prep.build_preprocessor()),
                ("gbr", GradientBoostingRegressor(n_estimators=300, max_depth=3, random_state=RANDOM_STATE))])
reg.fit(Xr_tr, yr_tr)
pred = reg.predict(Xr_te)
print(f"MAE: ${mean_absolute_error(yr_te, pred):,.0f}   R^2: {r2_score(yr_te, pred):.3f}")
""")

md("## 9. Final classifier comparison")

code(r"""
# Combine default + tuned + NN results into one table and plot.
all_rows = rows + tuned_rows + [max(nn_rows, key=lambda r: r['f1_macro'])]
final_table = ev.comparison_table(all_rows, save=True)
ev.plot_comparison_bars(final_table[final_table.model != "Baseline (majority)"].head(8))
final_table.round(4)
""")

md("""
## 10. Clustering (labels removed)

We drop the price-tier label, cluster on the preprocessed features, and compare
the discovered clusters to the true tiers with ARI / NMI / homogeneity.
""")

code(r"""
# Build a numeric design matrix (same preprocessing, no target leakage).
X_all, y_all = prep.feature_matrix(df)
Z = prep.build_preprocessor().fit_transform(X_all)
Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
print("design matrix:", Z.shape)

sel = cl.k_selection(Z)
sel.round(3)
""")

code(r"""
from sklearn.cluster import KMeans

# init experiment
for init in ["k-means++", "random"]:
    km = KMeans(n_clusters=3, init=init, n_init=10, random_state=RANDOM_STATE).fit(Z)
    print(f"init={init:10s} inertia={km.inertia_:,.0f}  ARI={cl.agreement(y_all, km.labels_)['ARI']:.3f}")

km = KMeans(n_clusters=3, n_init=10, random_state=RANDOM_STATE).fit(Z)
cl.pca_scatter(Z, km.labels_, y_all)
print("Agreement (KMeans k=3 vs true tiers):", {k: round(v, 3) for k, v in cl.agreement(y_all, km.labels_).items()})
cl.contingency(y_all, km.labels_)
""")

code(r"""
# Second algorithm: Agglomerative clustering with different linkages (on a sample for speed).
from sklearn.cluster import AgglomerativeClustering

rng = np.random.default_rng(RANDOM_STATE)
idx = rng.choice(len(Z), size=min(4000, len(Z)), replace=False)
Zs, ys = Z[idx], np.asarray(y_all)[idx]

for linkage in ["ward", "average", "complete"]:
    agg = AgglomerativeClustering(n_clusters=3, linkage=linkage).fit(Zs)
    a = cl.agreement(ys, agg.labels_)
    print(f"linkage={linkage:9s} ARI={a['ARI']:.3f}  NMI={a['NMI']:.3f}  homogeneity={a['homogeneity']:.3f}")
""")

md("""
## 11. Summary

- The comparison table (`results/model_comparison.csv`) ranks all classifiers by macro-F1.
- Tuning grids and chosen values are in `results/hyperparameter_tuning.csv`.
- NN architecture results are in `results/nn_architectures.csv`; feature-selection
  results in `results/feature_selection.csv`.
- Clustering agreement vs. true tiers and the contingency table are shown above;
  figures are saved under `results/`.

See `../report/REPORT.md` for the full written discussion.
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print("wrote", OUT, "with", len(cells), "cells")
