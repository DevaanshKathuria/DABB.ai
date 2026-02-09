"""Project configuration defaults and path helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    """Default configuration paths for Milestone 1."""

    model_path: Path = Path("models/model.joblib")
    reports_dir: Path = Path("reports")
    default_train_csv: Path = Path("data/raw/legal_docs_modified.csv")
    fallback_train_csv: Path = Path("data/demo/sample_training.csv")


def resolve_training_csv(requested_path: str | None, config: ProjectConfig) -> Path:
    """Resolve training CSV path with fallback demo dataset support."""
    if requested_path:
        return Path(requested_path)

    if config.default_train_csv.exists():
        return config.default_train_csv

    return config.fallback_train_csv
