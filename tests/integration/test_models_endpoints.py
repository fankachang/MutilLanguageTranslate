"""整合測試 - 模型清單/選擇/切換 endpoints（US1）

覆蓋：
- GET /api/v1/models/
- PUT /api/v1/models/selection/
- POST /api/v1/models/switch/

注意：本測試不應觸發真實大模型載入。
"""

import os
import sys
import json
from pathlib import Path
import importlib

import pytest

from tests.helpers.model_fixtures import create_model_dir

# 加入專案路徑（比照既有 tests/integration/test_api.py）
sys.path.insert(0, os.path.join(Path(__file__).parent, "../../translation_project"))


@pytest.mark.django_db
def test_get_models_lists_available_models(client, tmp_models_dir):
    create_model_dir(tmp_models_dir, "b", has_config=True)
    create_model_dir(tmp_models_dir, "a", has_config=True)
    create_model_dir(tmp_models_dir, "no_config", has_config=False)

    res = client.get("/api/v1/models/")
    assert res.status_code == 200

    data = res.json()
    assert "models" in data
    assert isinstance(data["models"], list)

    model_ids = [m.get("model_id") for m in data["models"]]
    assert model_ids == ["a", "b"]

    assert "active_model_id" in data
    assert "selected_model_id" in data


@pytest.mark.django_db
def test_put_selection_sets_selected_model_id(client, tmp_models_dir):
    create_model_dir(tmp_models_dir, "a", has_config=True)

    res = client.put(
        "/api/v1/models/selection/",
        data=json.dumps({"model_id": "a"}),
        content_type="application/json",
    )
    assert res.status_code == 200

    data = res.json()
    assert data["selected_model_id"] == "a"
    assert "active_model_id" in data
    assert "requires_switch" in data


@pytest.mark.django_db
def test_post_switch_switches_active_model(client, tmp_models_dir, monkeypatch):
    create_model_dir(tmp_models_dir, "a", has_config=True)

    # 避免觸發真實載入：以 monkeypatch 模擬切換結果
    model_service_module = importlib.import_module("translator.services.model_service")

    def _fake_switch_model(model_id: str, force: bool = False):
        _ = force
        return {
            "status": "switched",
            "active_model_id": model_id,
            "previous_model_id": None,
        }

    monkeypatch.setattr(
        model_service_module.ModelService,
        "switch_model",
        staticmethod(_fake_switch_model),
        raising=False,
    )

    res = client.post(
        "/api/v1/models/switch/",
        data=json.dumps({"model_id": "a", "force": False}),
        content_type="application/json",
    )
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "switched"
    assert data["active_model_id"] == "a"
