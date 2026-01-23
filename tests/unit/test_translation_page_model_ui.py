"""單元測試 - 翻譯頁模型選擇 UI（US1）

以模板片段驗證：
- 翻譯頁包含模型選擇下拉選單（UI 元件）
- 前端會呼叫 /api/v1/models/ 取得清單
- 翻譯請求會帶 model_id（向後相容：若未選擇則可不帶）
"""

from pathlib import Path


def test_index_template_contains_model_selector_and_api_calls():
    project_root = Path(__file__).resolve().parents[2]
    template_path = project_root / "translation_project" / "translator" / "templates" / "translator" / "index.html"

    html = template_path.read_text(encoding="utf-8")

    assert 'id="model-select"' in html
    assert "/api/v1/models/" in html
    assert "model_id" in html
