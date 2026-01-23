"""單元測試 - Containerfile runtime 設定（US3）

需求：Containerfile 不應硬依賴未安裝的 uvloop。

本專案 requirements 預設不強制安裝 uvloop，因此 Containerfile 的 uvicorn 啟動參數
不應包含 `--loop uvloop`。
"""

from pathlib import Path


def test_containerfile_does_not_require_uvloop():
    project_root = Path(__file__).resolve().parents[2]
    containerfile = project_root / "Containerfile"
    content = containerfile.read_text(encoding="utf-8")

    # 以最小條件鎖定：避免 uvicorn 強制指定 uvloop
    assert "--loop" not in content or "uvloop" not in content
    assert "uvloop" not in content
