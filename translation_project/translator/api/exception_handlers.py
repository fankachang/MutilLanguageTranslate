"""
多國語言翻譯系統 - API 例外處理器

本模組提供統一的 API 錯誤回應格式處理。
用於捕獲各種例外並轉換為標準的 JSON 錯誤回應。
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, Type

from django.http import JsonResponse

from translator.errors import (
    ErrorCode,
    TranslationError,
    get_error_message,
    get_http_status,
)

logger = logging.getLogger('translator')


class ValidationError(Exception):
    """驗證錯誤"""
    def __init__(self, code: str, message: str = None):
        self.code = code
        self.message = message or get_error_message(code)
        super().__init__(self.message)


class ServiceUnavailableError(Exception):
    """服務不可用錯誤"""
    def __init__(self, code: str = ErrorCode.SERVICE_UNAVAILABLE, message: str = None):
        self.code = code
        self.message = message or get_error_message(code)
        super().__init__(self.message)


class TimeoutError(Exception):
    """逾時錯誤"""
    def __init__(self, code: str = ErrorCode.TRANSLATION_TIMEOUT, message: str = None):
        self.code = code
        self.message = message or get_error_message(code)
        super().__init__(self.message)


class AccessDeniedError(Exception):
    """存取拒絕錯誤"""
    def __init__(self, code: str = ErrorCode.ACCESS_DENIED, message: str = None):
        self.code = code
        self.message = message or get_error_message(code)
        super().__init__(self.message)


def create_error_response(
    error_code: str,
    message: str = None,
    http_status: int = None,
    details: Any = None,
    request_id: str = None,
) -> JsonResponse:
    """
    建立標準化的錯誤回應
    
    Args:
        error_code: 錯誤代碼
        message: 錯誤訊息（可選，預設使用錯誤代碼對應的訊息）
        http_status: HTTP 狀態碼（可選，預設根據錯誤代碼決定）
        details: 額外的錯誤詳情（可選）
        request_id: 請求 ID（可選）
        
    Returns:
        JsonResponse: 標準化的錯誤回應
    """
    response_data = {
        'error': {
            'code': error_code,
            'message': message or get_error_message(error_code),
        }
    }
    
    if request_id:
        response_data['request_id'] = request_id
    
    if details:
        response_data['error']['details'] = details
    
    status = http_status or get_http_status(error_code)
    
    return JsonResponse(response_data, status=status)


def handle_api_exceptions(view_func: Callable) -> Callable:
    """
    API 視圖的例外處理裝飾器
    
    自動捕獲常見的例外並轉換為標準的 JSON 錯誤回應。
    
    使用方式：
        @handle_api_exceptions
        def my_view(request):
            ...
    
    Args:
        view_func: 要裝飾的視圖函數
        
    Returns:
        裝飾後的視圖函數
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
            
        except TranslationError as e:
            logger.warning(f"翻譯錯誤: {e.code} - {e.message}")
            return create_error_response(
                error_code=e.code,
                message=e.message,
                http_status=e.http_status,
            )
            
        except ValidationError as e:
            logger.warning(f"驗證錯誤: {e.code} - {e.message}")
            return create_error_response(
                error_code=e.code,
                message=e.message,
                http_status=400,
            )
            
        except ServiceUnavailableError as e:
            logger.error(f"服務不可用: {e.code} - {e.message}")
            return create_error_response(
                error_code=e.code,
                message=e.message,
                http_status=503,
            )
            
        except TimeoutError as e:
            logger.warning(f"請求逾時: {e.code} - {e.message}")
            return create_error_response(
                error_code=e.code,
                message=e.message,
                http_status=504,
            )
            
        except AccessDeniedError as e:
            logger.warning(f"存取被拒: {e.code} - {e.message}")
            return create_error_response(
                error_code=e.code,
                message=e.message,
                http_status=403,
            )
            
        except Exception as e:
            # 記錄未預期的錯誤
            logger.exception(f"API 發生未預期錯誤: {str(e)}")
            return create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                http_status=500,
            )
    
    return wrapper


class ExceptionHandler:
    """
    例外處理器類別
    
    提供更靈活的例外處理機制，支援自訂例外類型映射。
    """
    
    # 例外類型到錯誤代碼的映射
    EXCEPTION_MAPPINGS = {
        TranslationError: None,  # 使用例外自帶的代碼
        ValidationError: None,
        ServiceUnavailableError: None,
        TimeoutError: None,
        AccessDeniedError: None,
        ValueError: ErrorCode.VALIDATION_INVALID_LANGUAGE,
        TypeError: ErrorCode.INTERNAL_ERROR,
    }
    
    @classmethod
    def handle(cls, exception: Exception, request_id: str = None) -> JsonResponse:
        """
        處理例外並返回適當的錯誤回應
        
        Args:
            exception: 例外物件
            request_id: 請求 ID（可選）
            
        Returns:
            JsonResponse: 標準化的錯誤回應
        """
        exception_type = type(exception)
        
        # 檢查是否有自訂的錯誤代碼
        if hasattr(exception, 'code'):
            error_code = exception.code
            message = getattr(exception, 'message', None)
            http_status = getattr(exception, 'http_status', None)
        elif exception_type in cls.EXCEPTION_MAPPINGS:
            error_code = cls.EXCEPTION_MAPPINGS[exception_type]
            if error_code is None:
                error_code = ErrorCode.INTERNAL_ERROR
            message = str(exception)
            http_status = None
        else:
            error_code = ErrorCode.INTERNAL_ERROR
            message = None
            http_status = 500
        
        return create_error_response(
            error_code=error_code,
            message=message,
            http_status=http_status,
            request_id=request_id,
        )
    
    @classmethod
    def register(cls, exception_type: Type[Exception], error_code: str):
        """
        註冊新的例外類型映射
        
        Args:
            exception_type: 例外類別
            error_code: 對應的錯誤代碼
        """
        cls.EXCEPTION_MAPPINGS[exception_type] = error_code


def format_validation_errors(errors: dict) -> str:
    """
    格式化驗證錯誤字典為人類可讀的訊息
    
    Args:
        errors: 驗證錯誤字典 {field: [messages]}
        
    Returns:
        str: 格式化的錯誤訊息
    """
    messages = []
    for field, field_errors in errors.items():
        if isinstance(field_errors, list):
            for error in field_errors:
                messages.append(f"{field}: {error}")
        else:
            messages.append(f"{field}: {field_errors}")
    
    return "; ".join(messages)


# 預定義的錯誤回應工廠函數
def empty_text_error() -> JsonResponse:
    """返回文字為空的錯誤回應"""
    return create_error_response(ErrorCode.VALIDATION_EMPTY_TEXT)


def text_too_long_error() -> JsonResponse:
    """返回文字過長的錯誤回應"""
    return create_error_response(ErrorCode.VALIDATION_TEXT_TOO_LONG)


def same_language_error() -> JsonResponse:
    """返回來源與目標語言相同的錯誤回應"""
    return create_error_response(ErrorCode.VALIDATION_SAME_LANGUAGE)


def invalid_language_error() -> JsonResponse:
    """返回無效語言代碼的錯誤回應"""
    return create_error_response(ErrorCode.VALIDATION_INVALID_LANGUAGE)


def queue_full_error() -> JsonResponse:
    """返回佇列已滿的錯誤回應"""
    return create_error_response(ErrorCode.QUEUE_FULL)


def service_unavailable_error() -> JsonResponse:
    """返回服務不可用的錯誤回應"""
    return create_error_response(ErrorCode.SERVICE_UNAVAILABLE)


def timeout_error() -> JsonResponse:
    """返回逾時的錯誤回應"""
    return create_error_response(ErrorCode.TRANSLATION_TIMEOUT)


def model_not_loaded_error() -> JsonResponse:
    """返回模型未載入的錯誤回應"""
    return create_error_response(ErrorCode.MODEL_NOT_LOADED)


def access_denied_error() -> JsonResponse:
    """返回存取被拒的錯誤回應"""
    return create_error_response(ErrorCode.ACCESS_DENIED)


def internal_error() -> JsonResponse:
    """返回內部錯誤的錯誤回應"""
    return create_error_response(ErrorCode.INTERNAL_ERROR)
