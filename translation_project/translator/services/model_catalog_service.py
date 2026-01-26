from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from django.conf import settings

from translator.utils.model_id import validate_model_id

logger = logging.getLogger("translator")


@dataclass(frozen=True)
class ModelEntry:
    model_id: str
    display_name: str
    has_config: bool
    path: Path
    last_error_message: Optional[str] = None


class ModelCatalogService:
    """掃描 models/ 目錄以取得可用模型清單。

    最低可用門檻：`models/<model_id>/config.json` 存在且可讀取。
    """

    REQUIRED_CONFIG_FILENAME = "config.json"

    @classmethod
    def list_models(cls, models_dir: Optional[Path] = None) -> List[ModelEntry]:
        base_dir = Path(models_dir) if models_dir is not None else Path(settings.MODELS_DIR)

        if not base_dir.exists() or not base_dir.is_dir():
            logger.warning(f"模型目錄不存在或不可用: {base_dir}")
            return []

        entries: list[ModelEntry] = []
        for child in sorted(base_dir.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue

            try:
                model_id = validate_model_id(child.name)
            except Exception:
                logger.warning(f"略過不合法的模型目錄名稱: {child.name}")
                continue

            config_path = child / cls.REQUIRED_CONFIG_FILENAME
            if not config_path.is_file():
                continue

            try:
                config_path.open("rb").close()
            except Exception:
                continue

            entries.append(
                ModelEntry(
                    model_id=model_id,
                    display_name=model_id,
                    has_config=True,
                    path=child,
                )
            )

        return entries
