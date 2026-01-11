"""
多國語言翻譯系統 - 佇列服務

本模組負責請求佇列管理：
- 使用 threading.Lock 確保執行緒安全
- 並發控制（最大 100 並發）
- 等待佇列管理（最大 100 等待）
"""

import logging
import threading
from collections import deque
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from uuid import uuid4

from translator.enums import QueueStatus, TranslationStatus
from translator.models import QueueItem, TranslationRequest
from translator.utils.config_loader import ConfigLoader

logger = logging.getLogger('translator')


class QueueService:
    """
    請求佇列服務
    
    負責管理翻譯請求的並發控制與等待佇列。
    使用 threading.Lock 確保執行緒安全。
    """
    
    _instance: Optional['QueueService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化服務"""
        # 處理中的請求
        self._active_requests: Dict[str, QueueItem] = {}
        # 等待佇列
        self._waiting_queue: deque = deque()
        # 請求 ID 到 QueueItem 的映射（用於快速查詢）
        self._request_map: Dict[str, QueueItem] = {}
        
        logger.info("佇列服務已初始化")
    
    @classmethod
    def get_instance(cls) -> 'QueueService':
        """取得 QueueService 單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def acquire_slot(
        self,
        request: TranslationRequest
    ) -> Tuple[str, Dict[str, Any]]:
        """
        嘗試取得處理槽位
        
        Args:
            request: 翻譯請求
            
        Returns:
            (request_id, 結果字典)
            結果字典包含：
            - status: 'processing' | 'queued' | 'rejected'
            - queue_position: 佇列位置（若為 queued）
            - estimated_wait_seconds: 預估等待時間（若為 queued）
        """
        with self._lock:
            max_concurrent = ConfigLoader.get_max_concurrent()
            max_queue_size = ConfigLoader.get_max_queue_size()
            
            # 建立佇列項目
            queue_item = QueueItem(
                request_id=request.request_id,
                request=request,
                status=QueueStatus.QUEUED,
            )
            
            # 檢查是否可以直接處理
            if len(self._active_requests) < max_concurrent:
                queue_item.status = QueueStatus.PROCESSING
                queue_item.started_at = datetime.utcnow()
                
                self._active_requests[request.request_id] = queue_item
                self._request_map[request.request_id] = queue_item
                
                logger.debug(
                    f"請求 {request.request_id} 直接開始處理 "
                    f"(並發: {len(self._active_requests)}/{max_concurrent})"
                )
                
                return request.request_id, {
                    'status': TranslationStatus.PROCESSING,
                }
            
            # 檢查佇列是否已滿
            if len(self._waiting_queue) >= max_queue_size:
                logger.warning(
                    f"佇列已滿，拒絕請求 {request.request_id} "
                    f"(佇列: {len(self._waiting_queue)}/{max_queue_size})"
                )
                return request.request_id, {
                    'status': TranslationStatus.REJECTED,
                }
            
            # 加入等待佇列
            queue_item.queue_position = len(self._waiting_queue) + 1
            self._waiting_queue.append(queue_item)
            self._request_map[request.request_id] = queue_item
            
            # 預估等待時間（假設每個請求平均 3 秒）
            estimated_wait = queue_item.queue_position * 3
            
            logger.debug(
                f"請求 {request.request_id} 加入等待佇列 "
                f"(位置: {queue_item.queue_position})"
            )
            
            return request.request_id, {
                'status': TranslationStatus.PENDING,
                'queue_position': queue_item.queue_position,
                'estimated_wait_seconds': estimated_wait,
            }
    
    def release_slot(self, request_id: str) -> Optional[QueueItem]:
        """
        釋放處理槽位
        
        Args:
            request_id: 請求 ID
            
        Returns:
            下一個要處理的 QueueItem，若無則返回 None
        """
        with self._lock:
            # 從處理中移除
            if request_id in self._active_requests:
                completed_item = self._active_requests.pop(request_id)
                completed_item.status = QueueStatus.COMPLETED
                
                # 從映射中移除
                if request_id in self._request_map:
                    del self._request_map[request_id]
                
                logger.debug(
                    f"請求 {request_id} 處理完成 "
                    f"(剩餘並發: {len(self._active_requests)})"
                )
            
            # 檢查等待佇列是否有請求
            if self._waiting_queue:
                next_item = self._waiting_queue.popleft()
                next_item.status = QueueStatus.PROCESSING
                next_item.started_at = datetime.utcnow()
                next_item.queue_position = None
                
                self._active_requests[next_item.request_id] = next_item
                
                # 更新剩餘佇列的位置
                for i, item in enumerate(self._waiting_queue):
                    item.queue_position = i + 1
                
                logger.debug(
                    f"從佇列取出請求 {next_item.request_id} 開始處理"
                )
                
                return next_item
            
            return None
    
    def get_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        取得請求狀態
        
        Args:
            request_id: 請求 ID
            
        Returns:
            狀態字典，若請求不存在則返回 None
        """
        with self._lock:
            if request_id not in self._request_map:
                return None
            
            item = self._request_map[request_id]
            result = {
                'request_id': request_id,
                'status': item.status,
            }
            
            if item.queue_position is not None:
                result['queue_position'] = item.queue_position
            
            if item.started_at is not None:
                result['started_at'] = item.started_at.isoformat() + 'Z'
            
            return result
    
    def cancel_request(self, request_id: str) -> bool:
        """
        取消請求
        
        Args:
            request_id: 請求 ID
            
        Returns:
            是否成功取消
        """
        with self._lock:
            if request_id not in self._request_map:
                return False
            
            item = self._request_map[request_id]
            
            # 只能取消等待中的請求
            if item.status != QueueStatus.QUEUED:
                return False
            
            # 從等待佇列移除
            try:
                self._waiting_queue.remove(item)
                item.status = QueueStatus.CANCELLED
                del self._request_map[request_id]
                
                # 更新剩餘佇列的位置
                for i, q_item in enumerate(self._waiting_queue):
                    q_item.queue_position = i + 1
                
                logger.debug(f"請求 {request_id} 已取消")
                return True
            except ValueError:
                return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        取得佇列統計
        
        Returns:
            統計字典
        """
        with self._lock:
            return {
                'active_requests': len(self._active_requests),
                'queued_requests': len(self._waiting_queue),
                'max_concurrency': ConfigLoader.get_max_concurrent(),
                'max_queue_size': ConfigLoader.get_max_queue_size(),
            }
    
    def clear_all(self):
        """清空所有請求（測試用）"""
        with self._lock:
            self._active_requests.clear()
            self._waiting_queue.clear()
            self._request_map.clear()
            logger.info("已清空所有佇列")


# 方便外部使用的函數
def get_queue_service() -> QueueService:
    """取得 QueueService 單例實例"""
    return QueueService.get_instance()
