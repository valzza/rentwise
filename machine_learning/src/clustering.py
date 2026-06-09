"""Clustering helpers: k selection (elbow + silhouette), PCA-2D visualisation,
and agreement scoring between clusters and the true price tiers.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    completeness_score,
    homogeneity_score,
    normalized_mutual_info_score,
    silhouette_score,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RANDOM_STATE = 42


def _ensure_results() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def k_selection(X, k_range=range(2, 9), fname: str = "kmeans_selection.png") -> pd.DataFrame:
    """Sweep k for KMeans; record inertia (elbow) and silhouette. Saves a 2-panel plot."""
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE)
        labels = km.fit_predict(X)
        rows.append(
            {
                "k": k,
                "inertia": km.inertia_,
                "silhouette": silhouette_score(X, labels),
            }
        )
    df = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(df["k"], df["inertia"], "o-")
    axes[0].set(xlabel="k", ylabel="inertia", title="Elbow (inertia)")
    axes[1].plot(df["k"], df["silhouette"], "o-", color="darkorange")
    axes[1].set(xlabel="k", ylabel="silhouette", title="Silhouette score")
    fig.tight_layout()
    _ensure_results()
    fig.savefig(RESULTS_DIR / fname, dpi=120, bbox_inches="tight")
    plt.show()
    return df


def pca_scatter(X, cluster_labels, true_labels, fname: str = "clusters_pca.png") -> np.ndarray:
    """Project X to 2D via PCA and show clusters vs. true tiers side by side."""
    coords = PCA(n_components=2, random_state=RANDOM_STATE).fit_transform(X)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(coords[:, 0], coords[:, 1], c=cluster_labels, cmap="viridis", s=6, alpha=0.5)
    axes[0].set_title("KMeans clusters (PCA-2D)")

    codes, uniques = pd.factorize(pd.Series(true_labels))
    sc = axes[1].scatter(coords[:, 0], coords[:, 1], c=codes, cmap="coolwarm", s=6, alpha=0.5)
    axes[1].set_title("True price tiers (PCA-2D)")
    handles, _ = sc.legend_elements()
    axes[1].legend(handles, list(uniques), title="tier", fontsize=8)

    for ax in axes:
        ax.set(xlabel="PC1", ylabel="PC2")
    fig.tight_layout()
    _ensure_results()
    fig.savefig(RESULTS_DIR / fname, dpi=120, bbox_inches="tight")
    plt.show()
    return coords


def agreement(true_labels, cluster_labels) -> dict:
    """External validation: how well clusters match the true tiers."""
    return {
        "ARI": adjusted_rand_score(true_labels, cluster_labels),
        "NMI": normalized_mutual_info_score(true_labels, cluster_labels),
        "homogeneity": homogeneity_score(true_labels, cluster_labels),
        "completeness": completeness_score(true_labels, cluster_labels),
    }


def contingency(true_labels, cluster_labels) -> pd.DataFrame:
    """Crosstab of true tier vs. assigned cluster."""
    return pd.crosstab(
        pd.Series(true_labels, name="true_tier"),
        pd.Series(cluster_labels, name="cluster"),
    )