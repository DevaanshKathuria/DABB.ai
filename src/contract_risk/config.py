"""Project configuration defaults and path helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

try:  # pragma: no cover - optional runtime convenience for hosted deployments
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - dependency is optional at import time
    load_dotenv = None

if load_dotenv is not None:  # pragma: no cover - simple import-time convenience
    load_dotenv()


def _path_from_env(env_name: str, default: str) -> Path:
    """Read a path override from the environment."""
    override = os.getenv(env_name)
    return Path(override).expanduser() if override else Path(default)


@dataclass(frozen=True)
class ProjectConfig:
    """Default configuration paths for Milestone 2."""

    model_path: Path = field(default_factory=lambda: _path_from_env("DABB_MODEL_PATH", "models/model.joblib"))
    reports_dir: Path = field(default_factory=lambda: _path_from_env("DABB_REPORTS_DIR", "reports"))
    default_train_csv: Path = field(
        default_factory=lambda: _path_from_env("DABB_TRAINING_CSV", "data/raw/legal_docs_modified.csv")
    )
    fallback_train_csv: Path = field(
        default_factory=lambda: _path_from_env("DABB_FALLBACK_TRAINING_CSV", "data/demo/sample_training.csv")
    )


def resolve_training_csv(requested_path: str | None, config: ProjectConfig) -> Path:
    """Resolve training CSV path with fallback demo dataset support."""
    if requested_path:
        return Path(requested_path)

    if config.default_train_csv.exists():
        return config.default_train_csv

    return config.fallback_train_csv
