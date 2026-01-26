from __future__ import annotations
from translator.enums import ExecutionMode, ModelStatus
from translator.services.model_service import ModelService, get_model_service

import os
import sys
from pathlib import Path

# 加入專案路徑（比照 tests/integration）
sys.path.insert(0, os.path.join(
    Path(__file__).parent, "../../translation_project"))


class _DummyProvider:
    def unload(self):
        return None

    def get_status(self) -> str:
        return ModelStatus.LOADED

    def get_execution_mode(self) -> str:
        return ExecutionMode.CPU

    def is_loaded(self) -> bool:
        return True

    def get_error_message(self):
        return None

    def get_loading_progress(self) -> float:
        return 100.0


def test_unload_model_does_not_shadow_provider_instance_attr():
    service = get_model_service()

    # 清掉舊版 bug 可能留下的 instance attribute
    service.__dict__.pop("_provider", None)

    ModelService._provider = _DummyProvider()
    ModelService._provider_type = "local"
    ModelService._active_model_id = "Translategemma-12b-it"

    service.unload_model()

    assert ModelService._provider is None
    assert ModelService._provider_type is None
    assert ModelService._active_model_id is None
    assert "_provider" not in service.__dict__
