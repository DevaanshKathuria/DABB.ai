"""Model comparison utilities for baseline classifiers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier


def _build_pipeline(classifier: object) -> Pipeline:
    """Create a standard TF-IDF + classifier pipeline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=30000,
                ),
            ),
            ("classifier", classifier),
        ]
    )


def compare_baseline_models(
    train_texts: list[str],
    train_labels: list[str],
    test_texts: list[str],
    test_labels: list[str],
    output_dir: str | Path = "reports",
) -> pd.DataFrame:
    """Train and compare baseline classifiers on weighted P/R/F1 metrics."""
    candidates: dict[str, Pipeline] = {
        "LogisticRegression": _build_pipeline(
            LogisticRegression(max_iter=3000, class_weight="balanced", random_state=42)
        ),
        "LinearSVC": _build_pipeline(LinearSVC(class_weight="balanced", random_state=42)),
        "DecisionTree": _build_pipeline(
            DecisionTreeClassifier(max_depth=30, min_samples_leaf=2, random_state=42)
        ),
    }

    rows: list[dict[str, float | str]] = []

    for model_name, pipeline in candidates.items():
        pipeline.fit(train_texts, train_labels)
        preds = pipeline.predict(test_texts)

        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels,
            preds,
            average="weighted",
            zero_division=0,
        )

        rows.append(
            {
                "model": model_name,
                "precision_weighted": float(precision),
                "recall_weighted": float(recall),
                "f1_weighted": float(f1),
            }
        )

    result = pd.DataFrame(rows).sort_values(by="f1_weighted", ascending=False)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path / "model_comparison.csv", index=False)

    return result
