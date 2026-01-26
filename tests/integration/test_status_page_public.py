"""整合測試 - 狀態頁匿名可用（US2）

驗證：匿名使用者可直接開啟 /admin/status/（HTTP 200）。

注意：此頁面本身不走 /api/v1/admin/*，IP 白名單限制應只影響受保護的 API。
"""

import pytest


@pytest.mark.django_db
def test_status_page_is_public(client):
    res = client.get("/admin/status/")
    assert res.status_code == 200
