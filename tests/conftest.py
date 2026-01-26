from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def tmp_models_dir(tmp_path: Path, settings):
    """建立臨時 models 目錄並覆寫 Django settings.MODELS_DIR。"""
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    settings.MODELS_DIR = models_dir
    return models_dir
