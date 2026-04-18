"""Release smoke tests for hosted startup and fallback behavior."""

from __future__ import annotations

from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

import app
import streamlit_app
from contract_risk.config import ProjectConfig
from contract_risk.models import inference
from contract_risk.models.inference import load_or_train_model


def test_entrypoints_import_cleanly() -> None:
    """Hosted and local entrypoints should import without executing the app."""
    assert callable(app.render_app)
    assert callable(streamlit_app.main)


def test_project_config_reads_environment_overrides(monkeypatch, tmp_path) -> None:
    """Deployment-safe config overrides should resolve from environment variables."""
    monkeypatch.setenv("DABB_MODEL_PATH", str(tmp_path / "cached-model.joblib"))
    monkeypatch.setenv("DABB_REPORTS_DIR", str(tmp_path / "reports"))
    monkeypatch.setenv("DABB_TRAINING_CSV", str(tmp_path / "train.csv"))
    monkeypatch.setenv("DABB_FALLBACK_TRAINING_CSV", str(tmp_path / "fallback.csv"))

    config = ProjectConfig()

    assert config.model_path == tmp_path / "cached-model.joblib"
    assert config.reports_dir == tmp_path / "reports"
    assert config.default_train_csv == tmp_path / "train.csv"
    assert config.fallback_train_csv == tmp_path / "fallback.csv"


def test_load_or_train_model_continues_if_cache_write_fails(monkeypatch, tmp_path) -> None:
    """A write failure should not block a trained model from being returned."""
    frame = pd.DataFrame({"text": ["Hello contract clause"], "label": ["termination"]})

    class DummyModel:
        def predict(self, batch):
            return ["termination" for _ in batch]

    monkeypatch.setattr(inference, "load_training_dataframe", lambda csv_path: frame)
    monkeypatch.setattr(inference, "train_logreg_model", lambda texts, labels: DummyModel())

    def _boom(model, path):  # noqa: D401 - simple failure stub
        raise OSError("read only filesystem")

    monkeypatch.setattr(inference, "save_model", _boom)

    model = load_or_train_model(model_path=tmp_path / "cached-model.joblib")

    assert isinstance(model, DummyModel)


def test_milestone_two_pptx_artifact_is_valid() -> None:
    """The committed presentation should be a real 10-slide PowerPoint file."""
    pptx_path = Path("reports/milestone2_presentation/output.pptx")
    assert pptx_path.exists(), "Expected the final deck artifact to be checked in"
    assert zipfile.is_zipfile(pptx_path), "The deck artifact must be a valid PPTX archive"

    with zipfile.ZipFile(pptx_path) as archive:
        presentation_xml = archive.read("ppt/presentation.xml")

    root = ET.fromstring(presentation_xml)
    ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    slide_ids = root.findall(".//p:sldIdLst/p:sldId", ns)

    assert len(slide_ids) == 10
