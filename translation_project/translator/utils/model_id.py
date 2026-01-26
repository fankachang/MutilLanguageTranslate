from __future__ import annotations

import re

from translator.errors import ErrorCode, TranslationError


_INVALID_CHARS = re.compile(r"[\\/]|\x00")
_WINDOWS_RESERVED = re.compile(r"[:<>\"|?*]")


def validate_model_id(model_id: str) -> str:
    """驗證 model_id 是否安全且可作為單一資料夾名稱。

    規則（最小必要）：
    - 不可為空
    - 不可包含 `..`
    - 不可包含路徑分隔符（`/`、`\\`）
    - 不可為絕對路徑或包含磁碟代號（例如 `C:`）
    """
    if not isinstance(model_id, str) or not model_id.strip():
        raise TranslationError(ErrorCode.MODEL_INVALID_ID, "model_id 不可為空")

    model_id = model_id.strip()

    if model_id in {".", ".."} or ".." in model_id.split("/") or ".." in model_id.split("\\"):
        raise TranslationError(ErrorCode.MODEL_INVALID_ID, "model_id 不可包含 ..")

    if _INVALID_CHARS.search(model_id):
        raise TranslationError(
            ErrorCode.MODEL_INVALID_ID, "model_id 不可包含路徑分隔符")

    # Windows：避免磁碟代號/保留字元造成路徑穿越或解析歧義
    if _WINDOWS_RESERVED.search(model_id):
        raise TranslationError(ErrorCode.MODEL_INVALID_ID, "model_id 包含不允許的字元")

    # 盡量避免 ~ 這類常見 home shorthand
    if model_id.startswith("~"):
        raise TranslationError(
            ErrorCode.MODEL_INVALID_ID, "model_id 不可為絕對或特殊路徑")

    return model_id
