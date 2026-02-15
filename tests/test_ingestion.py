"""Tests for text ingestion robustness."""

from __future__ import annotations

from pathlib import Path

import pytest

from contract_risk.data.ingestion import (
    DocumentReadError,
    UnsupportedFileTypeError,
    extract_text_from_path,
    extract_text_from_upload,
)


def test_unsupported_extension_from_path(tmp_path: Path) -> None:
    invalid_file = tmp_path / "contract.docx"
    invalid_file.write_text("dummy", encoding="utf-8")

    with pytest.raises(UnsupportedFileTypeError):
        extract_text_from_path(invalid_file)


def test_empty_upload_raises_error() -> None:
    with pytest.raises(DocumentReadError):
        extract_text_from_upload("empty.txt", b"")


def test_corrupted_pdf_upload_raises_error() -> None:
    with pytest.raises(DocumentReadError):
        extract_text_from_upload("bad.pdf", b"not-a-real-pdf")
