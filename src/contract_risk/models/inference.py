"""Model loading and fallback training for inference."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from contract_risk.config import ProjectConfig
from contract_risk.data.loader import load_training_dataframe
from contract_risk.models.pipeline import load_model, save_model, train_logreg_model


def load_or_train_model(model_path: str | Path | None = None) -> object:
    """Load an existing model, or train one from available CSV data."""
    config = ProjectConfig()
    resolved_model_path = Path(model_path) if model_path else config.model_path

    if resolved_model_path.exists():
        return load_model(resolved_model_path)

    csv_path = config.default_train_csv if config.default_train_csv.exists() else config.fallback_train_csv
    dataset = load_training_dataframe(csv_path)
    model = train_logreg_model(dataset["text"].tolist(), dataset["label"].tolist())
    save_model(model, resolved_model_path)
    return model


def predict_clauses(model: object, clauses: Sequence[str], batch_size: int = 256) -> list[str]:
    """Predict clause types in batches to support long documents."""
    predictions: list[str] = []
    for start in range(0, len(clauses), batch_size):
        batch = list(clauses[start : start + batch_size])
        batch_preds = model.predict(batch)
        predictions.extend(str(item) for item in batch_preds)
    return predictions
