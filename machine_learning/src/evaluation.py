"""Evaluation helpers: per-model metrics, comparison table, confusion-matrix plots.

Metrics reported for every classifier: accuracy, precision, recall, F1
(macro + weighted) and the confusion matrix -- the assignment minimum.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


def _ensure_results() -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR


def score_model(name: str, y_true, y_pred) -> dict:
    """Return a one-row metrics dict for a fitted model's predictions."""
    return {
        "model": name,
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted", zero_division=0),
    }


def comparison_table(rows: list[dict], save: bool = True) -> pd.DataFrame:
    """Build (and optionally save) the cross-model comparison table, sorted by F1."""
    df = pd.DataFrame(rows).sort_values("f1_macro", ascending=False).reset_index(drop=True)
    if save:
        _ensure_results()
        df.to_csv(RESULTS_DIR / "model_comparison.csv", index=False)
    return df


def plot_confusion(y_true, y_pred, labels, title: str, fname: str | None = None) -> None:
    """Plot (and optionally save) a labelled confusion matrix."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels, yticklabels=labels, ax=ax, cbar=False,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    fig.tight_layout()
    if fname:
        _ensure_results()
        fig.savefig(RESULTS_DIR / fname, dpi=120, bbox_inches="tight")
    plt.show()


def text_report(y_true, y_pred) -> str:
    return classification_report(y_true, y_pred, zero_division=0)


def plot_comparison_bars(table: pd.DataFrame, fname: str = "model_comparison.png") -> None:
    """Grouped bar chart of accuracy/precision/recall/F1 per model."""
    metrics = ["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(table))
    width = 0.2
    for i, m in enumerate(metrics):
        ax.bar(x + i * width, table[m], width, label=m)
    ax.set_xticks(x + 1.5 * width)
    ax.set_xticklabels(table["model"], rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("score")
    ax.set_title("Classifier comparison")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    _ensure_results()
    fig.savefig(RESULTS_DIR / fname, dpi=120, bbox_inches="tight")
    plt.show()