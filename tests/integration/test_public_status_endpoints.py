"""整合測試 - 公開狀態 endpoints（US2）

驗證：匿名可存取 public 只讀狀態端點。
- GET /api/v1/status/
- GET /api/v1/statistics/
- GET /api/v1/model/load-progress/

這些端點不得回 401/403。
"""

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path,required_keys",
    [
        ("/api/v1/status/", {"status", "timestamp"}),
        ("/api/v1/statistics/", {"status", "statistics"}),
        ("/api/v1/model/load-progress/",
         {"status", "progress", "model_status", "loaded"}),
    ],
)
def test_public_status_endpoints_are_accessible(client, path, required_keys):
    res = client.get(path)
    assert res.status_code == 200

    data = res.json()
    assert required_keys.issubset(set(data.keys()))
