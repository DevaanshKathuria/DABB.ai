"""TF-IDF based training pipeline for clause type classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DEFAULT_MODEL_PATH = Path("models/model.joblib")


def build_logreg_pipeline() -> Pipeline:
    """Build the baseline TF-IDF + Logistic Regression pipeline."""
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
            (
                "classifier",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def train_logreg_model(texts: list[str], labels: list[str]) -> Pipeline:
    """Train the baseline model."""
    model = build_logreg_pipeline()
    model.fit(texts, labels)
    return model


def save_model(model: Any, path: str | Path = DEFAULT_MODEL_PATH) -> Path:
    """Persist model to disk in joblib format."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination)
    return destination


def load_model(path: str | Path = DEFAULT_MODEL_PATH) -> Any:
    """Load a previously trained model."""
    return joblib.load(path)
