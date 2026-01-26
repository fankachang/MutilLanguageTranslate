"""單元測試 - 管理頁面模型選擇 UI（US1）

以模板片段驗證：
- 管理頁面包含模型選擇下拉選單（UI 元件）
- 前端會呼叫 /api/v1/models/ 取得清單
- 翻譯請求會帶 model_id（向後相容：若未選擇則可不帶）

備註：模型選擇器已從翻譯頁面移到 /admin/status/ 頁面
"""

from pathlib import Path


def test_admin_status_template_contains_model_selector_and_api_calls():
    """測試 admin_status.html 包含模型選擇器和 API 呼叫"""
    project_root = Path(__file__).resolve().parents[2]
    template_path = project_root / "translation_project" / \
        "translator" / "templates" / "translator" / "admin_status.html"

    html = template_path.read_text(encoding="utf-8")

    # 檢查模型選擇器（admin-model-select）
    assert 'id="admin-model-select"' in html
    # 檢查 API 呼叫
    assert "/api/v1/models/" in html


def test_index_template_does_not_contain_model_selector():
    """測試翻譯頁（index.html）不再包含模型選擇器"""
    project_root = Path(__file__).resolve().parents[2]
    template_path = project_root / "translation_project" / \
        "translator" / "templates" / "translator" / "index.html"

    html = template_path.read_text(encoding="utf-8")

    # 翻譯頁應該不再有 model-select 選擇器
    assert 'id="model-select"' not in html
