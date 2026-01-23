"""整合測試 - 翻譯 API 支援 model_id（US1）

此測試只驗證：
- /api/v1/translate/ 能接收可選欄位 model_id
- model_id 會被傳遞到 service.translate(TranslationRequest)

注意：本測試不得觸發真實大模型載入。
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
def test_translate_request_passes_model_id_to_service(client, tmp_models_dir, monkeypatch):
    create_model_dir(tmp_models_dir, "a", has_config=True)

    views = importlib.import_module("translator.api.views")
    TranslationStatus = importlib.import_module("translator.enums").TranslationStatus
    TranslationResponse = importlib.import_module("translator.models").TranslationResponse

    captured = {}

    class StubTranslationService:
        def translate(self, request):
            captured["model_id"] = getattr(request, "model_id", None)
            return TranslationResponse(
                request_id="test-id",
                status=TranslationStatus.COMPLETED,
                processing_time_ms=1,
                execution_mode="cpu",
                translated_text="OK",
            )

    def _get_stub_service():
        return StubTranslationService()

    monkeypatch.setattr(views, "get_translation_service", _get_stub_service)

    res = client.post(
        "/api/v1/translate/",
        data=json.dumps(
            {
                "text": "Hello",
                "source_language": "en",
                "target_language": "zh-TW",
                "quality": "standard",
                "model_id": "a",
            }
        ),
        content_type="application/json",
    )

    assert res.status_code == 200
    assert captured.get("model_id") == "a"

    payload = res.json()
    assert payload["status"] == TranslationStatus.COMPLETED
    assert payload["translated_text"] == "OK"
