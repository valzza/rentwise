# Rental Price-Tier Classification & Clustering — Project Report

## 1. Introduction

The goal of this project is to gain practical experience applying machine-learning
algorithms to **real-world data**. We work with real US apartment rental listings and
study two related problems:

- **Classification (supervised):** given a listing's attributes (size, bedrooms,
  bathrooms, amenities, state, etc.), predict its **price tier** — `Budget`, `Mid`, or
  `Premium`. We implement, tune, and compare six classifiers spanning four algorithm
  families and benchmark them against a majority-class baseline.
- **Clustering (unsupervised):** with the price label removed, we group the listings
  and measure how well the discovered structure matches the true price tiers.

Predicting a price *tier* (rather than an exact rent) turns the rental-pricing problem
into a classification task with a naturally interpretable target and a 3-class structure
that the clustering step (k = 3) can be compared against. The same dataset also powers a
companion web application (RentWise), whose production price model is a gradient-boosting
**regressor**; we reproduce that regressor here as an explicit bridge between the two
projects.

## 2. Dataset Description

We use the **UCI *Apartment for Rent Classified*** dataset (UCI Machine Learning
Repository, id 555) — real classified rental listings from the United States. The
acquisition script (`src/download_data.py`) downloads the official archive and extracts
the 10,000-row version (the inner files are `.7z`-compressed, `;`-delimited, latin-1
encoded).

**Raw data:** 10,000 rows × 22 columns, including `bedrooms`, `bathrooms`,
`square_feet`, `amenities`, `pets_allowed`, `has_photo`, `price`, `price_type`,
`cityname`, `state`, `latitude`, `longitude`.

**Feature engineering** (`src/preprocessing.py`):

| Engineered feature | Type | Derivation |
|---|---|---|
| `square_feet` | numeric | as-is |
| `bedrooms` | numeric | as-is |
| `bathrooms` | numeric | as-is |
| `amenities_count` | numeric | count of comma-separated amenities |
| `state` | categorical | top-20 states kept, the rest collapsed to `OTHER` |
| `is_pet_friendly` | categorical (0/1) | `pets_allowed` not null/none |
| `has_photo_flag` | categorical (0/1) | listing has a photo (a listing-quality signal) |

**Cleaning:** coerce numerics; drop rows missing price/size/rooms; keep `price > 0` and
`square_feet > 0`; trim the 1st/99th percentile price tails and the top 1 % of sizes;
cap bedrooms ≤ 8 and bathrooms ≤ 6. This leaves **9,670 rows**.

**Target:** monthly rent is split into tertiles to form a balanced 3-class label —
`Budget` (3,235), `Mid` (3,257), `Premium` (3,178). Rents range from \$530 to \$4,995.
The class balance means **accuracy is meaningful** and the majority-class baseline sits
at ≈ 0.337.

*(See `results/eda_price.png` for the rent distribution and tier boundaries, and
`results/eda_corr.png` for numeric feature correlations.)*

## 3. Methodology

### 3.1 Preprocessing pipeline
All models share a scikit-learn `ColumnTransformer`: numeric features are median-imputed
and standardised (`StandardScaler`); categorical features are most-frequent-imputed and
one-hot encoded (`OneHotEncoder(handle_unknown="ignore")`). After encoding the design
matrix has **29 columns**. The data is split **80/20, stratified** on the price tier
with `random_state=42`. Encoding/scaling is fit on the training fold only (inside each
`Pipeline`), so there is no leakage.

### 3.2 Classifiers (four families)
| Model | Family |
|---|---|
| `KNeighborsClassifier` | distance-based |
| `DecisionTreeClassifier`, `RandomForestClassifier` | tree-based |
| `LogisticRegression` | linear |
| `MLPClassifier` | **neural network** |
| `GradientBoostingClassifier` | boosting (bridge to RentWise) |
| `DummyClassifier(most_frequent)` | baseline |

### 3.3 Hyperparameter tuning
Each classifier is tuned with `GridSearchCV` (5-fold, scoring = macro-F1). The tested
grids and selected values are logged to `results/hyperparameter_tuning.csv`:

| Model | Tested grid | Chosen | CV macro-F1 |
|---|---|---|---|
| KNN | `n_neighbors∈{5,15,25,35}`, `weights∈{uniform,distance}` | `n_neighbors=25, weights=distance` | 0.633 |
| DecisionTree | `max_depth∈{5,8,12,None}`, `min_samples_leaf∈{1,5,20}` | `max_depth=None, min_samples_leaf=20` | 0.615 |
| RandomForest | `n_estimators∈{200,400}`, `max_depth∈{None,12,20}` | `max_depth=20, n_estimators=200` | **0.650** |
| LogisticRegression | `C∈{0.1,1,10}` | `C=1.0` | 0.619 |
| GradientBoosting | `n_estimators∈{100,200}`, `max_depth∈{2,3}`, `lr∈{0.05,0.1}` | `n_estimators=200, max_depth=3, lr=0.1` | 0.648 |

### 3.4 Feature selection / dimensionality reduction
Using a Random Forest as the fixed estimator, we compare the full feature set against
`SelectKBest` (ANOVA-F, k = 6 and 10) and `PCA` (5 and 10 components).

### 3.5 Neural-network architectures
We vary the `MLPClassifier` depth, width and activation while keeping the shared
preprocessing: `(64,)`, `(128,64)`, `(128,64,32)` with ReLU, and `(128,64)` with tanh
(`alpha=1e-4`, up to 500 iterations).

### 3.6 Regression bridge
A `GradientBoostingRegressor` is trained on the **raw rent** (not the tier) to mirror the
RentWise production model, reported with MAE and R².

### 3.7 Clustering
With the label removed, the 29-column design matrix is clustered with **KMeans** (k
swept 2–8; elbow + silhouette; `k-means++` vs `random` init) and **Agglomerative
clustering** (ward / average / complete linkage). Clusters are projected to 2D with
**PCA** for visualisation and compared to the true tiers with ARI, NMI, homogeneity and
completeness, plus a contingency table.

## 4. Results

### 4.1 Classifier comparison
Full table in `results/model_comparison.csv`; chart in `results/model_comparison.png`.
Test-set highlights (sorted by macro-F1):

| Model | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) |
|---|---|---|---|---|
| **RandomForest (tuned)** | **0.639** | 0.641 | 0.639 | **0.640** |
| GradientBoosting (tuned) | 0.639 | 0.642 | 0.639 | 0.638 |
| KNN (default) | 0.634 | 0.637 | 0.635 | 0.633 |
| MLP `(64,)` ReLU | 0.632 | 0.631 | 0.632 | 0.630 |
| LogisticRegression | 0.616 | 0.611 | 0.616 | 0.611 |
| DecisionTree (default) | 0.609 | 0.638 | 0.608 | 0.608 |
| **Baseline (majority)** | 0.337 | 0.112 | 0.333 | 0.168 |

Every real classifier roughly **doubles** the baseline's accuracy and quadruples its
macro-F1. The tree ensembles (Random Forest, Gradient Boosting) lead, with KNN and the
small MLP close behind; the linear model and a single decision tree trail. Confusion
matrices (`results/cm_randomforest.png`, `results/cm_mlp.png`) show that almost all
errors are between **adjacent** tiers (Budget↔Mid, Mid↔Premium); the extreme tiers are
rarely confused with each other.

### 4.2 Feature selection / reduction (`results/feature_selection.csv`)
| Variant | Accuracy |
|---|---|
| All features | 0.624 |
| PCA (10 comps) | 0.600 |
| PCA (5 comps) | 0.552 |
| SelectKBest (k=10) | 0.562 |
| SelectKBest (k=6) | 0.536 |

The full feature set wins. Aggressive reduction costs 6–9 accuracy points; PCA with 10
components retains the most signal among the reduced variants.

### 4.3 Neural-network architectures (`results/nn_architectures.csv`)
| Architecture | Accuracy | F1 (macro) |
|---|---|---|
| `(64,)` ReLU | **0.632** | **0.630** |
| `(128,64)` ReLU | 0.622 | 0.622 |
| `(128,64,32)` ReLU | 0.618 | 0.615 |
| `(128,64)` tanh | 0.609 | 0.607 |

The **smallest** network performs best. Adding layers/units slightly *reduces* test
performance (mild overfitting on a modest, low-dimensional dataset), and ReLU beats tanh
at equal capacity.

### 4.4 Regression bridge
The `GradientBoostingRegressor` on raw rent achieves **MAE ≈ \$320** and **R² ≈ 0.53** on
the held-out set — a reasonable fit given that the listing features capture only part of
what drives rent (location quality, exact address, condition, photos, etc. are not fully
represented).

### 4.5 Clustering (`results/kmeans_selection.png`, `results/clusters_pca.png`)
- **k selection:** silhouette is highest at k = 2 (0.33) and falls as k grows; the
  inertia elbow is around k = 3–4. There is no strong, well-separated cluster structure.
- **KMeans (k = 3) vs. true tiers:** ARI = 0.058, NMI = 0.062, homogeneity = 0.061,
  completeness = 0.063 — **weak agreement**. Initialisation (`k-means++` vs `random`)
  made no difference.
- **Contingency table** (true tier × cluster):

  | true tier \ cluster | 0 | 1 | 2 |
  |---|---|---|---|
  | Budget | 320 | 2007 | 908 |
  | Mid | 996 | 1438 | 823 |
  | Premium | 1548 | 1184 | 446 |

  There is a *trend* — Premium concentrates in cluster 0, Budget in cluster 1 — but the
  clusters are far from a clean tier split.
- **Agglomerative clustering:** `ward` linkage agrees best (ARI = 0.053), `average` and
  `complete` are near zero, confirming the same conclusion.

## 5. Discussion

**Which classifier is best and why.** The tuned **Random Forest** and **Gradient
Boosting** models are the strongest (≈ 0.64 accuracy / macro-F1). Tree ensembles capture
non-linear interactions (e.g. a large studio in an expensive state) and handle the
mixed numeric/one-hot feature space well, without the feature-scaling sensitivity of KNN
or the linear-boundary limitation of Logistic Regression. The small MLP is competitive,
showing a neural network can match classical models here, but it has no advantage on a
small, low-dimensional, tabular problem — and the architecture sweep shows extra capacity
hurts rather than helps.

**Ceiling around ~0.64.** All models cluster near the same accuracy, which suggests the
limit is the **information in the features**, not the model. Tertile boundaries are sharp
cut-offs in a continuous quantity, so listings near a boundary are inherently ambiguous;
the regression R² of 0.53 tells the same story. Most misclassifications are between
adjacent tiers, which is the benign failure mode.

**Feature selection.** Reducing features never helped — the dataset already has few,
mostly informative features, so dropping any discards signal. This is a useful negative
result: dimensionality reduction is not always beneficial.

**Clustering vs. tiers.** The unsupervised structure only weakly matches the price tiers
(ARI ≈ 0.06). This is an honest and instructive finding: the natural groupings in the
feature space are driven more by **size and geography** than by the *imposed* price
tertiles, and price boundaries do not coincide with natural gaps in the data. Clustering
is therefore better read as *market segmentation* than as a way to recover the tiers.

## 6. Conclusion

On real US rental data, price-tier classification is learnable well above chance:
the best models (tuned Random Forest / Gradient Boosting) reach ≈ 0.64 macro-F1 versus a
0.17 baseline, with errors confined to neighbouring tiers. A compact neural network
matches the classical models but does not surpass them, and larger networks overfit. The
full feature set outperforms every reduced variant. Unsupervised clustering reveals real
structure but only weakly aligns with the price tiers, indicating that rent tiers are not
the dominant axis of natural variation in the listings. The accompanying gradient-boosting
regressor (MAE ≈ \$320, R² ≈ 0.53) is the model carried forward into the RentWise
application.

## 7. References

1. UCI Machine Learning Repository — *Apartment for Rent Classified* dataset (id 555).
   https://archive.ics.uci.edu/dataset/555/apartment+for+rent+classified
2. Pedregosa et al., *Scikit-learn: Machine Learning in Python*, JMLR 12 (2011).
3. scikit-learn documentation — model selection, preprocessing, clustering, metrics.
   https://scikit-learn.org/stable/
4. McKinney, *Data Structures for Statistical Computing in Python* (pandas), 2010.
5. Hunter, *Matplotlib: A 2D Graphics Environment*, 2007; Waskom, *seaborn*, 2021.