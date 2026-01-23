from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def create_model_dir(
    models_dir: Path,
    model_id: str,
    *,
    has_config: bool = True,
    config_content: dict[str, Any] | None = None,
) -> Path:
    """在 models_dir 下建立測試用模型目錄結構。

    預設會建立：
    - models/<model_id>/
    - models/<model_id>/config.json（可選）
    """
    model_path = models_dir / model_id
    model_path.mkdir(parents=True, exist_ok=True)

    if has_config:
        config_path = model_path / "config.json"
        config_path.write_text(
            json.dumps(config_content or {"_test": True}, ensure_ascii=False),
            encoding="utf-8",
        )

    return model_path
