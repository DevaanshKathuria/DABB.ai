"""CSV dataset loading for supervised clause classification."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

TEXT_COLUMN_CANDIDATES = ["text", "clause", "sentence", "content"]
LABEL_COLUMN_CANDIDATES = ["label", "category", "clause_type", "type"]


class DatasetSchemaError(ValueError):
    """Raised when no valid text/label columns are present."""


def _first_existing_column(columns: Iterable[str], candidates: list[str]) -> str:
    """Pick the first candidate column that exists in the dataframe."""
    column_set = set(columns)
    for column in candidates:
        if column in column_set:
            return column
    raise DatasetSchemaError(f"None of the expected columns found: {candidates}")


def load_training_dataframe(csv_path: str | Path) -> pd.DataFrame:
    """Load a training dataframe and normalize column names to text/label."""
    frame = pd.read_csv(csv_path)

    text_column = _first_existing_column(frame.columns, TEXT_COLUMN_CANDIDATES)
    label_column = _first_existing_column(frame.columns, LABEL_COLUMN_CANDIDATES)

    normalized = frame[[text_column, label_column]].copy()
    normalized.columns = ["text", "label"]
    normalized = normalized.dropna(subset=["text", "label"])

    normalized["text"] = normalized["text"].astype(str).str.strip()
    normalized["label"] = normalized["label"].astype(str).str.strip()
    normalized = normalized[(normalized["text"] != "") & (normalized["label"] != "")]

    if normalized.empty:
        raise DatasetSchemaError("No valid rows found after cleaning text and label columns.")

    return normalized
