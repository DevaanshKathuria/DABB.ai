"""Evaluation helpers for clause classification models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix


def evaluate_classifier(
    model: Any,
    texts: list[str],
    labels: list[str],
    output_dir: str | Path = "reports",
    prefix: str = "logreg",
) -> dict[str, float]:
    """Evaluate a classifier and persist metrics + confusion matrix artifacts."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    predictions = model.predict(texts)
    report = classification_report(labels, predictions, output_dict=True, zero_division=0)

    summary_metrics = {
        "precision_weighted": float(report["weighted avg"]["precision"]),
        "recall_weighted": float(report["weighted avg"]["recall"]),
        "f1_weighted": float(report["weighted avg"]["f1-score"]),
    }

    metrics_frame = pd.DataFrame(report).transpose()
    metrics_file = output_path / f"{prefix}_classification_report.csv"
    metrics_frame.to_csv(metrics_file)

    labels_sorted = sorted(set(labels) | set(predictions))
    matrix = confusion_matrix(labels, predictions, labels=labels_sorted)

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels_sorted,
        yticklabels=labels_sorted,
    )
    plt.title(f"Confusion Matrix - {prefix}")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    matrix_file = output_path / f"{prefix}_confusion_matrix.png"
    plt.savefig(matrix_file, dpi=200)
    plt.close()

    summary_file = output_path / f"{prefix}_summary_metrics.csv"
    pd.DataFrame([summary_metrics]).to_csv(summary_file, index=False)

    return summary_metrics
