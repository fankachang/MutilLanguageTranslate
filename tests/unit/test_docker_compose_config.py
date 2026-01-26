"""單元測試 - docker-compose.yaml 配置（US3）

驗證：
- ports: 8000:8000
- volumes: models/config/logs 掛載
- healthcheck: GET /api/health/

本測試採字串檢查，避免額外引入 YAML 解析依賴。
"""

from pathlib import Path


def test_docker_compose_has_required_ports_volumes_and_healthcheck():
    project_root = Path(__file__).resolve().parents[2]
    compose_file = project_root / "docker-compose.yaml"
    content = compose_file.read_text(encoding="utf-8")

    assert "\"8000:8000\"" in content or "8000:8000" in content

    assert "./models:/app/models" in content
    assert "./logs:/app/logs" in content
    assert "./config:/app/config" in content

    assert "/api/health/" in content
