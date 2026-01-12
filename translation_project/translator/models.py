"""
多國語言翻譯系統 - 資料類別定義

本模組定義系統中使用的所有資料類別，包括：
- Language: 語言定義
- TranslationRequest: 翻譯請求
- TranslationResponse: 翻譯回應
- QueueItem: 佇列項目
- SystemStatus: 系統狀態
- TranslationStatistics: 翻譯統計
- MinuteSnapshot: 分鐘快照（用於統計）
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass
class Language:
    """
    代表系統支援的翻譯語言
    
    Attributes:
        code: 語言代碼，如 "zh-TW", "en"
        name: 本地名稱，如 "繁體中文"
        name_en: 英文名稱，如 "Traditional Chinese"
        is_enabled: 是否啟用
        sort_order: 顯示排序
    """
    code: str
    name: str
    name_en: str
    is_enabled: bool = True
    sort_order: int = 0
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'code': self.code,
            'name': self.name,
            'name_en': self.name_en,
            'is_enabled': self.is_enabled,
            'sort_order': self.sort_order,
        }


@dataclass
class TranslationRequest:
    """
    代表一次翻譯操作的輸入
    
    Attributes:
        text: 待翻譯文字（1-10,000 字元）
        target_language: 目標語言代碼
        source_language: 來源語言代碼或 "auto"
        quality: 翻譯品質 (fast/standard/high)
        request_id: 唯一識別碼
        client_ip: 請求來源 IP
        received_at: 請求接收時間
        created_at: 建立時間（別名）
    """
    text: str
    target_language: str
    source_language: str = "auto"
    quality: str = "standard"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    client_ip: str = ""
    received_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def created_at(self) -> datetime:
        """建立時間（received_at 的別名）"""
        return self.received_at
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'request_id': self.request_id,
            'text': self.text,
            'source_language': self.source_language,
            'target_language': self.target_language,
            'quality': self.quality,
            'client_ip': self.client_ip,
            'received_at': self.received_at.isoformat(),
        }


@dataclass
class TranslationResponse:
    """
    代表翻譯結果
    
    Attributes:
        request_id: 對應的請求 ID
        status: 處理狀態 (pending/processing/completed/failed/timeout/rejected)
        processing_time_ms: 處理時間（毫秒）
        execution_mode: 執行模式 (gpu/cpu)
        completed_at: 完成時間
        translated_text: 翻譯結果（成功時）
        detected_language: 偵測到的語言（自動偵測時）
        confidence_score: 語言偵測信心分數 (0.0-1.0)
        error_code: 錯誤代碼（失敗時）
        error_message: 錯誤訊息（失敗時）
    """
    request_id: str
    status: str
    processing_time_ms: int
    execution_mode: str
    completed_at: datetime = field(default_factory=datetime.utcnow)
    translated_text: Optional[str] = None
    detected_language: Optional[str] = None
    confidence_score: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        result = {
            'request_id': self.request_id,
            'status': self.status,
            'processing_time_ms': self.processing_time_ms,
            'execution_mode': self.execution_mode,
        }
        
        if self.translated_text is not None:
            result['translated_text'] = self.translated_text
        
        if self.detected_language is not None:
            result['detected_language'] = self.detected_language
            
        if self.confidence_score is not None:
            result['confidence_score'] = self.confidence_score
            
        if self.error_code is not None:
            result['error'] = {
                'code': self.error_code,
                'message': self.error_message or '',
            }
            
        return result


@dataclass
class QueueItem:
    """
    代表佇列中的請求
    
    Attributes:
        request_id: 唯一識別碼
        request: 翻譯請求物件
        status: 佇列狀態 (queued/processing/completed/cancelled)
        queued_at: 加入佇列時間
        started_at: 開始處理時間
        queue_position: 佇列位置（等待中時）
    """
    request_id: str
    request: TranslationRequest
    status: str
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    queue_position: Optional[int] = None
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        result = {
            'request_id': self.request_id,
            'status': self.status,
            'queued_at': self.queued_at.isoformat(),
        }
        
        if self.started_at is not None:
            result['started_at'] = self.started_at.isoformat()
            
        if self.queue_position is not None:
            result['queue_position'] = self.queue_position
            
        return result


@dataclass
class SystemStatus:
    """
    代表系統監控資訊
    
    Attributes:
        is_running: 系統是否運行中
        model_status: 模型狀態 (not_loaded/loading/loaded/error)
        execution_mode: 當前執行模式 (gpu/cpu)
        active_requests: 處理中的請求數
        queued_requests: 等待中的請求數
        max_concurrency: 最大並發數
        max_queue_size: 最大佇列容量
        memory_usage_mb: 記憶體使用量 (MB)
        cpu_usage_percent: CPU 使用率 (%)
        uptime_seconds: 系統執行時間（秒）
        last_updated: 最後更新時間
        gpu_memory_usage_mb: GPU 記憶體使用量 (MB)，無 GPU 時為 None
    """
    is_running: bool
    model_status: str
    execution_mode: str
    active_requests: int
    queued_requests: int
    max_concurrency: int
    max_queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float
    uptime_seconds: int
    last_updated: datetime
    gpu_memory_usage_mb: Optional[float] = None
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        # 格式化運行時間
        hours, remainder = divmod(self.uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        result = {
            'system': {
                'is_running': self.is_running,
                'uptime': uptime_str,
                'last_updated': self.last_updated.isoformat() + 'Z',
            },
            'model': {
                'status': self.model_status,
                'name': 'TAIDE-LX-7B',
                'execution_mode': self.execution_mode,
            },
            'resources': {
                'memory_usage_mb': self.memory_usage_mb,
                'cpu_usage_percent': self.cpu_usage_percent,
            },
            'queue': {
                'active_requests': self.active_requests,
                'queued_requests': self.queued_requests,
                'max_concurrency': self.max_concurrency,
                'max_queue_size': self.max_queue_size,
            },
        }
        
        if self.gpu_memory_usage_mb is not None:
            result['resources']['gpu_memory_usage_mb'] = self.gpu_memory_usage_mb
            
        return result


@dataclass
class TranslationStatistics:
    """
    代表 24 小時內的翻譯統計
    
    Attributes:
        period_start: 統計期間開始時間
        period_end: 統計期間結束時間
        total_requests: 總請求數
        successful_requests: 成功請求數
        failed_requests: 失敗請求數
        success_rate: 成功率 (%)
        average_processing_time_ms: 平均處理時間（毫秒）
    """
    period_start: datetime
    period_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_processing_time_ms: float
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'period': {
                'start': self.period_start.isoformat() + 'Z',
                'end': self.period_end.isoformat() + 'Z',
            },
            'summary': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': self.success_rate,
                'average_processing_time_ms': self.average_processing_time_ms,
            },
        }


@dataclass
class MinuteSnapshot:
    """
    用於統計滑動視窗的內部結構
    
    Attributes:
        timestamp: 時間戳（格式：YYYYMMDDHHMM）
        total: 該分鐘請求數
        success: 該分鐘成功數
        total_time_ms: 該分鐘總處理時間
    """
    timestamp: str
    total: int = 0
    success: int = 0
    total_time_ms: int = 0
    
    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            'timestamp': self.timestamp,
            'total': self.total,
            'success': self.success,
            'total_time_ms': self.total_time_ms,
        }
