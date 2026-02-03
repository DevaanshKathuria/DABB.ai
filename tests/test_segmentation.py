"""Tests for clause segmentation."""

from contract_risk.features.segmentation import segment_clauses


def test_segment_by_numbered_patterns() -> None:
    text = (
        "1 Confidentiality Each party shall keep data confidential.\n"
        "2 Termination Either party may terminate with notice.\n"
        "3 Liability Neither party is liable for indirect damages."
    )
    clauses = segment_clauses(text)
    assert len(clauses) == 3
    assert clauses[0].startswith("1 Confidentiality")


def test_segment_with_lettered_patterns() -> None:
    text = "(a) Payment due in 15 days.\n(b) Late fee applies.\n(c) Taxes extra."
    clauses = segment_clauses(text, min_chars=10)
    assert len(clauses) >= 2


def test_fallback_sentence_chunking() -> None:
    text = "This is first sentence. This is second sentence. This is third sentence."
    clauses = segment_clauses(text)
    assert len(clauses) >= 1


def test_merge_tiny_fragments() -> None:
    text = "1 Scope.\n2 Confidentiality obligations are strict and survive termination."
    clauses = segment_clauses(text, min_chars=25)
    assert len(clauses) == 1
