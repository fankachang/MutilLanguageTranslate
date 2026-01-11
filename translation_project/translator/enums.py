"""
多國語言翻譯系統 - 列舉值定義

本模組定義系統中使用的所有列舉值，包括：
- QualityMode: 翻譯品質模式
- TranslationStatus: 翻譯狀態
- QueueStatus: 佇列狀態
- ExecutionMode: 執行模式
- ModelStatus: 模型狀態
"""


class QualityMode:
    """
    翻譯品質模式
    
    - FAST: 快速模式，較低品質但速度快
    - STANDARD: 標準模式（預設）
    - HIGH: 高品質模式，較高品質但速度慢
    """
    FAST = "fast"
    STANDARD = "standard"
    HIGH = "high"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """檢查值是否為有效的品質模式"""
        return value in (cls.FAST, cls.STANDARD, cls.HIGH)
    
    @classmethod
    def get_all(cls) -> list:
        """取得所有品質模式"""
        return [cls.FAST, cls.STANDARD, cls.HIGH]


class TranslationStatus:
    """
    翻譯狀態
    
    - PENDING: 等待中
    - PROCESSING: 處理中
    - COMPLETED: 完成
    - FAILED: 失敗
    - TIMEOUT: 逾時
    - REJECTED: 拒絕（佇列已滿）
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    
    @classmethod
    def is_final(cls, status: str) -> bool:
        """檢查是否為最終狀態"""
        return status in (cls.COMPLETED, cls.FAILED, cls.TIMEOUT, cls.REJECTED)


class QueueStatus:
    """
    佇列狀態
    
    - QUEUED: 佇列中等待
    - PROCESSING: 處理中
    - COMPLETED: 完成
    - CANCELLED: 取消
    """
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExecutionMode:
    """
    執行模式
    
    - GPU: GPU 模式（較快）
    - CPU: CPU 模式（降級）
    """
    GPU = "gpu"
    CPU = "cpu"


class ModelStatus:
    """
    模型狀態
    
    - NOT_LOADED: 未載入
    - LOADING: 載入中
    - LOADED: 已載入
    - ERROR: 錯誤
    """
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
