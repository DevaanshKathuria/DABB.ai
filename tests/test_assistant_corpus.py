"""Tests for the legal guidance corpus loader."""

from contract_risk.assistant.corpus import load_legal_guidance_corpus


def test_legal_guidance_corpus_loads() -> None:
    records = load_legal_guidance_corpus()
    assert len(records) >= 5
    assert any(record.topic == "force majeure" for record in records)


def test_corpus_search_text_includes_source_context() -> None:
    records = load_legal_guidance_corpus()
    first = records[0]
    assert first.source_name
    assert first.source_url.startswith("https://")
    assert first.search_text
