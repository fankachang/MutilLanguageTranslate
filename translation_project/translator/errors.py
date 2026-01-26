"""
多國語言翻譯系統 - 錯誤代碼定義

本模組定義系統中使用的所有錯誤代碼與對應的中文訊息
"""

from typing import Dict, Tuple


class ErrorCode:
    """
    錯誤代碼常數

    驗證錯誤 (400)：
    - VALIDATION_EMPTY_TEXT: 原文為空
    - VALIDATION_TEXT_TOO_LONG: 超過 10,000 字元
    - VALIDATION_SAME_LANGUAGE: 來源與目標語言相同
    - VALIDATION_INVALID_LANGUAGE: 無效的語言代碼

    服務錯誤 (503/504)：
    - QUEUE_FULL: 請求佇列已滿
    - SERVICE_UNAVAILABLE: 翻譯服務無法使用
    - TRANSLATION_TIMEOUT: 翻譯逾時
    - MODEL_NOT_LOADED: 模型未載入
    - NETWORK_ERROR: 網路連線失敗

    權限錯誤 (403)：
    - ACCESS_DENIED: IP 位址不在白名單中

    模型切換/查找錯誤：
    - MODEL_NOT_FOUND: 找不到指定模型
    - MODEL_INVALID_ID: model_id 不合法
    - MODEL_SWITCH_IN_PROGRESS: 模型切換中
    - MODEL_SWITCH_REJECTED: 切換被拒絕（政策/忙碌）
    - MODEL_SWITCH_FAILED: 切換失敗

    內部錯誤 (500)：
    - INTERNAL_ERROR: 內部錯誤
    """
    # 驗證錯誤
    VALIDATION_EMPTY_TEXT = "VALIDATION_EMPTY_TEXT"
    VALIDATION_TEXT_TOO_LONG = "VALIDATION_TEXT_TOO_LONG"
    VALIDATION_SAME_LANGUAGE = "VALIDATION_SAME_LANGUAGE"
    VALIDATION_INVALID_LANGUAGE = "VALIDATION_INVALID_LANGUAGE"

    # 服務錯誤
    QUEUE_FULL = "QUEUE_FULL"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TRANSLATION_TIMEOUT = "TRANSLATION_TIMEOUT"
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    NETWORK_ERROR = "NETWORK_ERROR"

    # 模型切換/查找
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_INVALID_ID = "MODEL_INVALID_ID"
    MODEL_SWITCH_IN_PROGRESS = "MODEL_SWITCH_IN_PROGRESS"
    MODEL_SWITCH_REJECTED = "MODEL_SWITCH_REJECTED"
    MODEL_SWITCH_FAILED = "MODEL_SWITCH_FAILED"

    # 權限錯誤
    ACCESS_DENIED = "ACCESS_DENIED"

    # 內部錯誤
    INTERNAL_ERROR = "INTERNAL_ERROR"


# 錯誤訊息對照表：代碼 -> (中文訊息, HTTP 狀態碼)
ERROR_MESSAGES: Dict[str, Tuple[str, int]] = {
    # 驗證錯誤 (400)
    ErrorCode.VALIDATION_EMPTY_TEXT: (
        "請輸入要翻譯的文字",
        400
    ),
    ErrorCode.VALIDATION_TEXT_TOO_LONG: (
        "文字長度超過 10,000 字元，請縮短後再試",
        400
    ),
    ErrorCode.VALIDATION_SAME_LANGUAGE: (
        "來源語言與目標語言不可相同",
        400
    ),
    ErrorCode.VALIDATION_INVALID_LANGUAGE: (
        "無效的語言代碼",
        400
    ),

    # 服務錯誤 (503/504)
    ErrorCode.QUEUE_FULL: (
        "系統繁忙，請稍後再試",
        503
    ),
    ErrorCode.SERVICE_UNAVAILABLE: (
        "翻譯服務暫時無法使用，請稍後再試",
        503
    ),
    ErrorCode.TRANSLATION_TIMEOUT: (
        "翻譯逾時，請嘗試縮短文字長度或稍後再試",
        504
    ),
    ErrorCode.MODEL_NOT_LOADED: (
        "翻譯模型尚未載入，請稍後再試",
        503
    ),
    ErrorCode.NETWORK_ERROR: (
        "網路連線失敗，請檢查網路狀態",
        503
    ),

    # 權限錯誤 (403)
    ErrorCode.ACCESS_DENIED: (
        "IP 位址不在白名單中",
        403
    ),

    # 模型切換/查找
    ErrorCode.MODEL_INVALID_ID: (
        "模型識別不合法",
        400
    ),
    ErrorCode.MODEL_NOT_FOUND: (
        "找不到指定模型",
        404
    ),
    ErrorCode.MODEL_SWITCH_IN_PROGRESS: (
        "模型切換中，請稍後再試",
        409
    ),
    ErrorCode.MODEL_SWITCH_REJECTED: (
        "模型切換被拒絕，請稍後再試",
        409
    ),
    ErrorCode.MODEL_SWITCH_FAILED: (
        "模型切換失敗",
        500
    ),

    # 內部錯誤 (500)
    ErrorCode.INTERNAL_ERROR: (
        "系統內部錯誤，請聯繫管理員",
        500
    ),
}


def get_error_message(code: str) -> str:
    """
    取得錯誤代碼對應的中文訊息

    Args:
        code: 錯誤代碼

    Returns:
        中文錯誤訊息
    """
    if code in ERROR_MESSAGES:
        return ERROR_MESSAGES[code][0]
    return ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR][0]


def get_http_status(code: str) -> int:
    """
    取得錯誤代碼對應的 HTTP 狀態碼

    Args:
        code: 錯誤代碼

    Returns:
        HTTP 狀態碼
    """
    if code in ERROR_MESSAGES:
        return ERROR_MESSAGES[code][1]
    return ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR][1]


class TranslationError(Exception):
    """
    翻譯錯誤例外類別

    Attributes:
        code: 錯誤代碼
        message: 錯誤訊息
        http_status: HTTP 狀態碼
    """
    def __init__(self, code: str, message: str = None):
        self.code = code
        self.message = message or get_error_message(code)
        self.http_status = get_http_status(code)
        super().__init__(self.message)

    def __str__(self) -> str:
        """字串表示"""
        return f"{self.code}: {self.message}"

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'code': self.code,
            'message': self.message,
        }
