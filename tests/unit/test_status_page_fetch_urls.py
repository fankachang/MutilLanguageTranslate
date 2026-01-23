"""單元測試 - 狀態頁模板 fetch URL 改為 public endpoints（US2）

驗證：
- 狀態頁模板不再用 /api/v1/admin/status/ 與 /api/v1/admin/statistics/ 來抓資料
- 改用 public endpoints：/api/v1/status/、/api/v1/statistics/、/api/v1/model/load-progress/

注意：具副作用的 admin 操作（例如 POST 觸發載入）仍可保留在 /api/v1/admin/*。
"""

from pathlib import Path


def test_admin_status_template_uses_public_endpoints_for_read():
    project_root = Path(__file__).resolve().parents[2]
    template_path = project_root / "translation_project" / \
        "translator" / "templates" / "translator" / "admin_status.html"

    html = template_path.read_text(encoding="utf-8")

    assert "/api/v1/status/" in html
    assert "/api/v1/statistics/" in html
    assert "/api/v1/model/load-progress/" in html

    assert "/api/v1/admin/status/" not in html
    assert "/api/v1/admin/statistics/" not in html
