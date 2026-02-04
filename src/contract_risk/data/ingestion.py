"""Text extraction helpers for contract documents."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    """Raised when an unsupported file extension is supplied."""


def extract_text_from_txt(path: str | Path, encoding: str = "utf-8") -> str:
    """Extract text from a UTF-8 text file."""
    return Path(path).read_text(encoding=encoding).strip()


def extract_text_from_pdf(file_obj: BinaryIO) -> str:
    """Extract text from a PDF file-like object."""
    reader = PdfReader(file_obj)
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(page for page in pages if page).strip()


def extract_text_from_path(path: str | Path) -> str:
    """Extract text based on file extension from a local path."""
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix == ".txt":
        return extract_text_from_txt(source)
    if suffix == ".pdf":
        with source.open("rb") as handle:
            return extract_text_from_pdf(handle)

    raise UnsupportedFileTypeError(f"Unsupported file extension: {suffix}")


def extract_text_from_upload(file_name: str, payload: bytes) -> str:
    """Extract text from uploaded bytes based on file name extension."""
    suffix = Path(file_name).suffix.lower()

    if suffix == ".txt":
        return payload.decode("utf-8", errors="ignore").strip()
    if suffix == ".pdf":
        return extract_text_from_pdf(BytesIO(payload))

    raise UnsupportedFileTypeError(f"Unsupported upload type: {suffix}")
