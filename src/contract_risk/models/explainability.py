"""Explainability helpers for linear TF-IDF models."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


class ExplainabilityError(ValueError):
    """Raised when a model cannot be explained with linear coefficients."""


def _extract_components(model: Pipeline) -> tuple[Any, Any]:
    """Extract vectorizer and classifier from sklearn pipeline."""
    if not hasattr(model, "named_steps"):
        raise ExplainabilityError("Expected a sklearn Pipeline with named steps.")

    vectorizer = model.named_steps.get("tfidf")
    classifier = model.named_steps.get("classifier")

    if vectorizer is None or classifier is None:
        raise ExplainabilityError("Pipeline must contain 'tfidf' and 'classifier' steps.")

    if not hasattr(classifier, "coef_"):
        raise ExplainabilityError("Classifier does not expose linear coefficients.")

    return vectorizer, classifier


def top_features_by_class(model: Pipeline, top_n: int = 10) -> pd.DataFrame:
    """Return top weighted features per class for linear classifiers."""
    vectorizer, classifier = _extract_components(model)

    feature_names = np.asarray(vectorizer.get_feature_names_out())
    class_names = np.asarray(classifier.classes_)

    rows: list[dict[str, str | float]] = []

    for class_index, class_name in enumerate(class_names):
        coef = classifier.coef_[class_index]
        top_indices = np.argsort(coef)[-top_n:][::-1]
        for rank, idx in enumerate(top_indices, start=1):
            rows.append(
                {
                    "class_label": str(class_name),
                    "rank": rank,
                    "feature": str(feature_names[idx]),
                    "weight": float(coef[idx]),
                }
            )

    return pd.DataFrame(rows)


def explain_text_prediction(model: Pipeline, text: str, top_n: int = 5) -> pd.DataFrame:
    """Return top contributing features for a single predicted class."""
    vectorizer, classifier = _extract_components(model)

    text_vector = vectorizer.transform([text])
    prediction = model.predict([text])[0]

    class_indices = np.where(classifier.classes_ == prediction)[0]
    if len(class_indices) == 0:
        raise ExplainabilityError("Predicted class not found in classifier classes.")

    class_index = int(class_indices[0])
    coef = classifier.coef_[class_index]

    row = text_vector.toarray()[0]
    non_zero_indices = np.where(row > 0)[0]
    if len(non_zero_indices) == 0:
        return pd.DataFrame(
            [{"prediction": str(prediction), "feature": "<none>", "contribution": 0.0}]
        )

    contributions = row[non_zero_indices] * coef[non_zero_indices]
    ranked = np.argsort(contributions)[-top_n:][::-1]

    feature_names = np.asarray(vectorizer.get_feature_names_out())
    rows: list[dict[str, str | float]] = []

    for idx in ranked:
        feature_idx = int(non_zero_indices[idx])
        rows.append(
            {
                "prediction": str(prediction),
                "feature": str(feature_names[feature_idx]),
                "contribution": float(contributions[idx]),
            }
        )

    return pd.DataFrame(rows)
