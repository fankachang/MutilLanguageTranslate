"""
日誌記錄工具 - Logger Utility

提供統一的日誌記錄功能：
- 翻譯請求日誌（包含請求詳情、耗時、結果）
- 錯誤日誌（包含堆疊追蹤、上下文）
- 效能日誌（處理時間、資源使用）
- 安全日誌（IP 存取記錄）
"""

import functools
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Optional

from django.http import HttpRequest


class TranslatorLogger:
    """
    翻譯系統專用日誌記錄器
    
    提供結構化的日誌記錄功能
    """
    
    def __init__(self, name: str = 'translator'):
        """
        初始化日誌記錄器
        
        Args:
            name: 日誌記錄器名稱
        """
        self.logger = logging.getLogger(name)
    
    def log_translation_request(
        self,
        request_id: str,
        text_length: int,
        source_language: str,
        target_language: str,
        quality: str,
        client_ip: str,
    ):
        """
        記錄翻譯請求開始
        
        Args:
            request_id: 請求 ID
            text_length: 文字長度
            source_language: 來源語言
            target_language: 目標語言
            quality: 品質模式
            client_ip: 客戶端 IP
        """
        self.logger.info(
            f"[翻譯請求] request_id={request_id} "
            f"text_length={text_length} "
            f"source={source_language} target={target_language} "
            f"quality={quality} ip={client_ip}"
        )
    
    def log_translation_result(
        self,
        request_id: str,
        success: bool,
        processing_time_ms: float,
        detected_language: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """
        記錄翻譯結果
        
        Args:
            request_id: 請求 ID
            success: 是否成功
            processing_time_ms: 處理時間（毫秒）
            detected_language: 偵測到的語言（可選）
            error_code: 錯誤代碼（失敗時）
            error_message: 錯誤訊息（失敗時）
        """
        if success:
            self.logger.info(
                f"[翻譯完成] request_id={request_id} "
                f"success=true processing_time_ms={processing_time_ms:.2f} "
                f"detected_language={detected_language or 'N/A'}"
            )
        else:
            self.logger.warning(
                f"[翻譯失敗] request_id={request_id} "
                f"success=false processing_time_ms={processing_time_ms:.2f} "
                f"error_code={error_code} error_message={error_message}"
            )
    
    def log_queue_status(
        self,
        request_id: str,
        queue_position: int,
        queue_size: int,
        estimated_wait: float,
    ):
        """
        記錄佇列狀態
        
        Args:
            request_id: 請求 ID
            queue_position: 佇列位置
            queue_size: 佇列大小
            estimated_wait: 預估等待時間（秒）
        """
        self.logger.info(
            f"[佇列狀態] request_id={request_id} "
            f"position={queue_position} queue_size={queue_size} "
            f"estimated_wait_seconds={estimated_wait:.1f}"
        )
    
    def log_model_load(
        self,
        model_name: str,
        execution_mode: str,
        load_time_seconds: float,
    ):
        """
        記錄模型載入
        
        Args:
            model_name: 模型名稱
            execution_mode: 執行模式
            load_time_seconds: 載入時間（秒）
        """
        self.logger.info(
            f"[模型載入] model={model_name} "
            f"mode={execution_mode} load_time_seconds={load_time_seconds:.2f}"
        )
    
    def log_model_unload(self, model_name: str):
        """
        記錄模型卸載
        
        Args:
            model_name: 模型名稱
        """
        self.logger.info(f"[模型卸載] model={model_name}")
    
    def log_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        request_id: Optional[str] = None,
    ):
        """
        記錄錯誤
        
        Args:
            error: 例外物件
            context: 額外上下文（可選）
            request_id: 請求 ID（可選）
        """
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        context_str = ""
        if context:
            context_str = " context=" + str(context)
        
        request_str = ""
        if request_id:
            request_str = f" request_id={request_id}"
        
        self.logger.error(
            f"[錯誤]{request_str} "
            f"type={error_type} message={error_message}{context_str}\n"
            f"Stack trace:\n{stack_trace}"
        )
    
    def log_security_event(
        self,
        event_type: str,
        client_ip: str,
        details: Optional[str] = None,
        allowed: bool = True,
    ):
        """
        記錄安全事件
        
        Args:
            event_type: 事件類型（access_denied, rate_limited 等）
            client_ip: 客戶端 IP
            details: 詳細資訊（可選）
            allowed: 是否允許
        """
        level = logging.INFO if allowed else logging.WARNING
        status = "allowed" if allowed else "denied"
        details_str = f" details={details}" if details else ""
        
        self.logger.log(
            level,
            f"[安全事件] type={event_type} ip={client_ip} "
            f"status={status}{details_str}"
        )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[dict] = None,
    ):
        """
        記錄效能指標
        
        Args:
            operation: 操作名稱
            duration_ms: 耗時（毫秒）
            metadata: 額外元資料（可選）
        """
        metadata_str = ""
        if metadata:
            metadata_str = " " + " ".join(f"{k}={v}" for k, v in metadata.items())
        
        self.logger.debug(
            f"[效能] operation={operation} "
            f"duration_ms={duration_ms:.2f}{metadata_str}"
        )
    
    def log_health_check(
        self,
        status: str,
        checks: dict,
    ):
        """
        記錄健康檢查結果
        
        Args:
            status: 整體狀態
            checks: 各項檢查結果
        """
        checks_str = " ".join(f"{k}={v.get('status', 'unknown')}" for k, v in checks.items())
        
        level = logging.INFO if status == 'healthy' else logging.WARNING
        self.logger.log(
            level,
            f"[健康檢查] status={status} {checks_str}"
        )


def log_request(logger: Optional[TranslatorLogger] = None):
    """
    請求日誌裝飾器
    
    記錄 API 請求的開始和結束
    
    Args:
        logger: TranslatorLogger 實例（可選）
    """
    if logger is None:
        logger = TranslatorLogger()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            start_time = time.time()
            
            # 取得請求資訊
            method = request.method
            path = request.path
            client_ip = get_client_ip(request)
            
            logger.logger.debug(
                f"[API 請求開始] method={method} path={path} ip={client_ip}"
            )
            
            try:
                response = func(request, *args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                status_code = response.status_code
                
                logger.logger.debug(
                    f"[API 請求完成] method={method} path={path} "
                    f"status={status_code} duration_ms={duration_ms:.2f}"
                )
                
                return response
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_error(e, context={
                    'method': method,
                    'path': path,
                    'ip': client_ip,
                    'duration_ms': duration_ms,
                })
                
                raise
        
        return wrapper
    
    return decorator


def log_operation(operation_name: str, logger: Optional[TranslatorLogger] = None):
    """
    操作日誌裝飾器
    
    記錄函數執行的開始和結束時間
    
    Args:
        operation_name: 操作名稱
        logger: TranslatorLogger 實例（可選）
    """
    if logger is None:
        logger = TranslatorLogger()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(operation_name, duration_ms)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_error(e, context={
                    'operation': operation_name,
                    'duration_ms': duration_ms,
                })
                raise
        
        return wrapper
    
    return decorator


def get_client_ip(request: HttpRequest) -> str:
    """
    取得客戶端 IP
    
    Args:
        request: HTTP 請求
    
    Returns:
        str: 客戶端 IP 地址
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# 全域日誌記錄器實例
_translator_logger: Optional[TranslatorLogger] = None


def get_translator_logger() -> TranslatorLogger:
    """
    取得 TranslatorLogger 單例
    
    Returns:
        TranslatorLogger: 日誌記錄器實例
    """
    global _translator_logger
    
    if _translator_logger is None:
        _translator_logger = TranslatorLogger()
    
    return _translator_logger
