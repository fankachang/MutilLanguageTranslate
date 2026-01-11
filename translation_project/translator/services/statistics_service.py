"""
多國語言翻譯系統 - 統計服務

本模組負責翻譯統計管理：
- 滑動視窗統計（24 小時）
- 分鐘快照儲存
- 成功率與平均處理時間計算
"""

import logging
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from django.core.cache import caches

from translator.models import MinuteSnapshot, TranslationStatistics

logger = logging.getLogger('translator')


class StatisticsService:
    """
    統計服務
    
    負責收集與計算翻譯統計資料，使用 24 小時滑動視窗。
    """
    
    _instance: Optional['StatisticsService'] = None
    _lock = threading.Lock()
    
    # 統計視窗大小（分鐘）
    WINDOW_SIZE_MINUTES = 24 * 60  # 24 小時
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化服務"""
        # 使用 Django Cache 儲存統計
        self._cache = caches['statistics']
        # 快照字典（記憶體快取）
        self._snapshots: Dict[str, MinuteSnapshot] = {}
        logger.info("統計服務已初始化")
    
    @classmethod
    def get_instance(cls) -> 'StatisticsService':
        """取得 StatisticsService 單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _get_minute_key(self, dt: datetime = None) -> str:
        """
        取得分鐘鍵值（格式：YYYYMMDDHHMM）
        
        Args:
            dt: 時間，預設為當前時間
            
        Returns:
            分鐘鍵值字串
        """
        if dt is None:
            dt = datetime.utcnow()
        return dt.strftime('%Y%m%d%H%M')
    
    def record_request(
        self,
        success: bool,
        processing_time_ms: int,
    ):
        """
        記錄一次請求
        
        Args:
            success: 是否成功
            processing_time_ms: 處理時間（毫秒）
        """
        with self._lock:
            minute_key = self._get_minute_key()
            
            if minute_key not in self._snapshots:
                self._snapshots[minute_key] = MinuteSnapshot(
                    timestamp=minute_key,
                )
            
            snapshot = self._snapshots[minute_key]
            snapshot.total += 1
            snapshot.total_time_ms += processing_time_ms
            
            if success:
                snapshot.success += 1
            
            logger.debug(
                f"記錄請求: 成功={success}, 時間={processing_time_ms}ms, "
                f"分鐘快照總計={snapshot.total}"
            )
            
            # 清理過期的快照
            self._cleanup_old_snapshots()
    
    def _cleanup_old_snapshots(self):
        """清理超過視窗大小的舊快照"""
        cutoff = datetime.utcnow() - timedelta(minutes=self.WINDOW_SIZE_MINUTES)
        cutoff_key = self._get_minute_key(cutoff)
        
        keys_to_remove = [
            key for key in self._snapshots.keys()
            if key < cutoff_key
        ]
        
        for key in keys_to_remove:
            del self._snapshots[key]
    
    def get_statistics(self) -> TranslationStatistics:
        """
        取得 24 小時統計
        
        Returns:
            TranslationStatistics 物件
        """
        with self._lock:
            now = datetime.utcnow()
            period_start = now - timedelta(hours=24)
            
            total_requests = 0
            successful_requests = 0
            total_time_ms = 0
            
            # 計算視窗內的統計
            cutoff_key = self._get_minute_key(period_start)
            
            for key, snapshot in self._snapshots.items():
                if key >= cutoff_key:
                    total_requests += snapshot.total
                    successful_requests += snapshot.success
                    total_time_ms += snapshot.total_time_ms
            
            failed_requests = total_requests - successful_requests
            
            # 計算成功率
            success_rate = (
                (successful_requests / total_requests * 100)
                if total_requests > 0 else 0.0
            )
            
            # 計算平均處理時間
            avg_processing_time = (
                (total_time_ms / total_requests)
                if total_requests > 0 else 0.0
            )
            
            return TranslationStatistics(
                period_start=period_start,
                period_end=now,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                success_rate=round(success_rate, 2),
                average_processing_time_ms=round(avg_processing_time, 2),
            )
    
    def get_hourly_breakdown(self) -> List[Dict[str, Any]]:
        """
        取得每小時分解統計
        
        Returns:
            每小時統計列表
        """
        with self._lock:
            now = datetime.utcnow()
            hourly_stats = defaultdict(lambda: {
                'total': 0,
                'success': 0,
                'total_time_ms': 0,
            })
            
            # 按小時彙總
            for key, snapshot in self._snapshots.items():
                hour_key = key[:10]  # YYYYMMDDHH
                hourly_stats[hour_key]['total'] += snapshot.total
                hourly_stats[hour_key]['success'] += snapshot.success
                hourly_stats[hour_key]['total_time_ms'] += snapshot.total_time_ms
            
            # 轉換為列表格式
            result = []
            for hour_key in sorted(hourly_stats.keys(), reverse=True)[:24]:
                stats = hourly_stats[hour_key]
                
                # 解析小時時間
                try:
                    hour_dt = datetime.strptime(hour_key, '%Y%m%d%H')
                except ValueError:
                    continue
                
                success_rate = (
                    (stats['success'] / stats['total'] * 100)
                    if stats['total'] > 0 else 0.0
                )
                
                avg_time = (
                    (stats['total_time_ms'] / stats['total'])
                    if stats['total'] > 0 else 0.0
                )
                
                result.append({
                    'hour': hour_dt.isoformat() + 'Z',
                    'requests': stats['total'],
                    'success_rate': round(success_rate, 2),
                    'avg_processing_time_ms': round(avg_time, 2),
                })
            
            return result
    
    def get_full_statistics(self) -> Dict[str, Any]:
        """
        取得完整統計（含每小時分解）
        
        Returns:
            完整統計字典
        """
        stats = self.get_statistics()
        hourly = self.get_hourly_breakdown()
        
        result = stats.to_dict()
        result['hourly_breakdown'] = hourly
        
        return result
    
    def reset(self):
        """重設所有統計（測試用）"""
        with self._lock:
            self._snapshots.clear()
            logger.info("已重設所有統計")


# 方便外部使用的函數
def get_statistics_service() -> StatisticsService:
    """取得 StatisticsService 單例實例"""
    return StatisticsService.get_instance()
