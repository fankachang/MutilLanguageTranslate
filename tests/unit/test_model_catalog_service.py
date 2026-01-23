"""單元測試 - ModelCatalogService

覆蓋規則：
- 只列出 `models/<model_id>/config.json` 存在且可讀的模型
- 目錄名稱需通過 `validate_model_id()`（例如：以 `~` 開頭應被略過）
"""

import os
import sys

import pytest

# 加入專案路徑（比照既有 unit tests 的做法）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../translation_project"))


def test_list_models_empty_dir_returns_empty_list(tmp_models_dir):
    from translator.services.model_catalog_service import ModelCatalogService

    models = ModelCatalogService.list_models()
    assert models == []


def test_list_models_filters_invalid_and_requires_config(tmp_models_dir):
    from translator.services.model_catalog_service import ModelCatalogService
    from tests.helpers.model_fixtures import create_model_dir

    create_model_dir(tmp_models_dir, "b", has_config=True)
    create_model_dir(tmp_models_dir, "a", has_config=True)
    create_model_dir(tmp_models_dir, "no_config", has_config=False)

    # `validate_model_id()` 目前會拒絕以 ~ 開頭的 model_id
    create_model_dir(tmp_models_dir, "~bad", has_config=True)

    models = ModelCatalogService.list_models()
    assert [m.model_id for m in models] == ["a", "b"]

    for entry in models:
        assert entry.has_config is True
        assert entry.path.name == entry.model_id
        assert entry.display_name == entry.model_id
