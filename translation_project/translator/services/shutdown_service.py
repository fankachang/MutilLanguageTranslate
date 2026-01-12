"""
優雅停止服務 - Graceful Shutdown Service

處理系統關閉流程：
- SIGTERM/SIGINT 信號處理
- 等待進行中的請求完成
- 120 秒超時強制終止
- 清理資源（模型、連線等）
"""

import asyncio
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger('translator')


class ShutdownService:
    """
    優雅停止服務
    
    管理應用程式的關閉流程，確保所有進行中的請求都能完成
    """
    
    # 預設超時時間（秒）
    DEFAULT_TIMEOUT = 120
    
    # 關閉階段
    PHASE_RUNNING = 'running'
    PHASE_STOPPING = 'stopping'
    PHASE_STOPPED = 'stopped'
    
    def __init__(self):
        """初始化優雅停止服務"""
        self._phase = self.PHASE_RUNNING
        self._shutdown_started: Optional[datetime] = None
        self._timeout = self.DEFAULT_TIMEOUT
        self._pending_requests: int = 0
        self._lock = threading.Lock()
        self._shutdown_callbacks: list[Callable] = []
        self._original_sigterm_handler = None
        self._original_sigint_handler = None
    
    @property
    def is_shutting_down(self) -> bool:
        """是否正在關閉中"""
        return self._phase != self.PHASE_RUNNING
    
    @property
    def phase(self) -> str:
        """取得當前關閉階段"""
        return self._phase
    
    @property
    def pending_requests(self) -> int:
        """取得進行中的請求數量"""
        with self._lock:
            return self._pending_requests
    
    @property
    def remaining_timeout(self) -> float:
        """取得剩餘超時時間（秒）"""
        if not self._shutdown_started:
            return self._timeout
        
        elapsed = (datetime.now() - self._shutdown_started).total_seconds()
        return max(0, self._timeout - elapsed)
    
    def register_signal_handlers(self):
        """
        註冊信號處理器
        
        處理 SIGTERM 和 SIGINT（Ctrl+C）信號
        """
        # Windows 不支援 SIGTERM，只處理 SIGINT
        try:
            self._original_sigterm_handler = signal.signal(
                signal.SIGTERM, 
                self._signal_handler
            )
            logger.info("已註冊 SIGTERM 信號處理器")
        except (ValueError, OSError) as e:
            logger.warning(f"無法註冊 SIGTERM 處理器: {e}")
        
        try:
            self._original_sigint_handler = signal.signal(
                signal.SIGINT,
                self._signal_handler
            )
            logger.info("已註冊 SIGINT 信號處理器")
        except (ValueError, OSError) as e:
            logger.warning(f"無法註冊 SIGINT 處理器: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        信號處理函數
        
        Args:
            signum: 信號編號
            frame: 當前堆疊幀
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"收到 {signal_name} 信號，開始優雅停止...")
        
        # 啟動關閉流程（非同步，避免阻塞主線程）
        shutdown_thread = threading.Thread(
            target=self.shutdown,
            name="ShutdownThread",
            daemon=False
        )
        shutdown_thread.start()
    
    def register_callback(self, callback: Callable):
        """
        註冊關閉回調函數
        
        Args:
            callback: 關閉時要執行的函數
        """
        self._shutdown_callbacks.append(callback)
        logger.debug(f"已註冊關閉回調: {callback.__name__}")
    
    def request_started(self):
        """標記一個請求開始處理"""
        with self._lock:
            self._pending_requests += 1
            logger.debug(f"請求開始，進行中: {self._pending_requests}")
    
    def request_finished(self):
        """標記一個請求完成處理"""
        with self._lock:
            self._pending_requests = max(0, self._pending_requests - 1)
            logger.debug(f"請求完成，進行中: {self._pending_requests}")
    
    def shutdown(self, timeout: Optional[float] = None):
        """
        執行優雅停止
        
        Args:
            timeout: 超時時間（秒），None 使用預設值
        """
        if self._phase != self.PHASE_RUNNING:
            logger.warning("已經在關閉流程中，忽略重複呼叫")
            return
        
        self._phase = self.PHASE_STOPPING
        self._shutdown_started = datetime.now()
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        
        logger.info(f"開始優雅停止流程，超時: {self._timeout} 秒")
        logger.info(f"目前進行中的請求: {self.pending_requests}")
        
        # 等待進行中的請求完成
        start_time = time.time()
        poll_interval = 0.5  # 輪詢間隔
        
        while self.pending_requests > 0:
            elapsed = time.time() - start_time
            
            if elapsed >= self._timeout:
                logger.warning(
                    f"超時 {self._timeout} 秒，強制終止 "
                    f"（剩餘 {self.pending_requests} 個請求未完成）"
                )
                break
            
            remaining = self._timeout - elapsed
            logger.info(
                f"等待請求完成... 進行中: {self.pending_requests}, "
                f"剩餘時間: {remaining:.1f} 秒"
            )
            
            time.sleep(min(poll_interval, remaining))
        
        if self.pending_requests == 0:
            logger.info("所有請求已完成")
        
        # 執行關閉回調
        self._execute_callbacks()
        
        # 標記為已停止
        self._phase = self.PHASE_STOPPED
        
        elapsed = time.time() - start_time
        logger.info(f"優雅停止完成，耗時: {elapsed:.2f} 秒")
    
    def _execute_callbacks(self):
        """執行所有關閉回調"""
        logger.info(f"執行 {len(self._shutdown_callbacks)} 個關閉回調...")
        
        for callback in self._shutdown_callbacks:
            try:
                logger.debug(f"執行回調: {callback.__name__}")
                callback()
            except Exception as e:
                logger.error(f"關閉回調執行失敗 ({callback.__name__}): {e}")
    
    def get_status(self) -> dict:
        """
        取得關閉狀態
        
        Returns:
            dict: 關閉狀態資訊
        """
        return {
            'phase': self._phase,
            'is_shutting_down': self.is_shutting_down,
            'pending_requests': self.pending_requests,
            'remaining_timeout': self.remaining_timeout,
            'shutdown_started': (
                self._shutdown_started.isoformat() 
                if self._shutdown_started else None
            ),
        }


# 全域單例
_shutdown_service: Optional[ShutdownService] = None


def get_shutdown_service() -> ShutdownService:
    """
    取得 ShutdownService 單例
    
    Returns:
        ShutdownService: 優雅停止服務實例
    """
    global _shutdown_service
    
    if _shutdown_service is None:
        _shutdown_service = ShutdownService()
    
    return _shutdown_service


def initialize_shutdown_service() -> ShutdownService:
    """
    初始化並啟動優雅停止服務
    
    Returns:
        ShutdownService: 已初始化的服務實例
    """
    service = get_shutdown_service()
    service.register_signal_handlers()
    
    # 註冊模型服務的清理回調
    try:
        from translator.services.model_service import get_model_service
        
        def cleanup_model():
            logger.info("清理翻譯模型...")
            model_service = get_model_service()
            model_service.unload_model()
        
        service.register_callback(cleanup_model)
    except ImportError:
        logger.warning("無法匯入 model_service，跳過模型清理回調")
    
    # 註冊佇列服務的清理回調
    try:
        from translator.services.queue_service import get_queue_service
        
        def cleanup_queue():
            logger.info("清理翻譯佇列...")
            queue_service = get_queue_service()
            queue_service.clear()
        
        service.register_callback(cleanup_queue)
    except ImportError:
        logger.warning("無法匯入 queue_service，跳過佇列清理回調")
    
    logger.info("優雅停止服務已初始化")
    return service
