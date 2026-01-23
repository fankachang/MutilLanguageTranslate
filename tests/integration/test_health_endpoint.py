"""整合測試 - 健康檢查端點（US3）

驗證：GET /api/health/ 回 200（不依賴容器）。
"""

import pytest


@pytest.mark.django_db
def test_health_endpoint_returns_200(client):
    res = client.get("/api/health/")
    assert res.status_code == 200

    data = res.json()
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
