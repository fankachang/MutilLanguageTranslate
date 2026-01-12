"""
多國語言翻譯系統 - 系統監控服務

本模組負責監控系統資源使用狀況：
- CPU 使用率
- 記憶體使用率
- GPU VRAM 使用率（如果有）
- 系統執行時間
"""

import logging
import os
import platform
import time
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger('translator')


class MonitorService:
    """
    系統監控服務
    
    提供系統資源使用狀況的查詢功能。
    """
    
    def __init__(self):
        self._start_time = time.time()
        self._process = psutil.Process() if PSUTIL_AVAILABLE else None
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        取得系統基本資訊
        
        Returns:
            系統資訊字典
        """
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
        }
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """
        取得 CPU 使用資訊
        
        Returns:
            CPU 資訊字典
        """
        if not PSUTIL_AVAILABLE:
            return {
                'available': False,
                'error': 'psutil 未安裝',
            }
        
        try:
            # 系統整體 CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # 每個 CPU 核心的使用率
            per_cpu = psutil.cpu_percent(percpu=True)
            
            # 程序 CPU 使用率
            process_cpu = self._process.cpu_percent(interval=0.1) if self._process else 0
            
            return {
                'available': True,
                'percent': cpu_percent,
                'count_physical': cpu_count,
                'count_logical': cpu_count_logical,
                'per_cpu': per_cpu,
                'process_percent': process_cpu,
            }
        except Exception as e:
            logger.error(f"取得 CPU 資訊失敗: {e}")
            return {
                'available': False,
                'error': str(e),
            }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        取得記憶體使用資訊
        
        Returns:
            記憶體資訊字典
        """
        if not PSUTIL_AVAILABLE:
            return {
                'available': False,
                'error': 'psutil 未安裝',
            }
        
        try:
            # 系統記憶體
            mem = psutil.virtual_memory()
            
            # 程序記憶體
            process_mem = self._process.memory_info() if self._process else None
            
            return {
                'available': True,
                'total_bytes': mem.total,
                'total_gb': round(mem.total / (1024**3), 2),
                'available_bytes': mem.available,
                'available_gb': round(mem.available / (1024**3), 2),
                'used_bytes': mem.used,
                'used_gb': round(mem.used / (1024**3), 2),
                'percent': mem.percent,
                'process_rss_bytes': process_mem.rss if process_mem else 0,
                'process_rss_mb': round(process_mem.rss / (1024**2), 2) if process_mem else 0,
                'process_vms_bytes': process_mem.vms if process_mem else 0,
                'process_vms_mb': round(process_mem.vms / (1024**2), 2) if process_mem else 0,
            }
        except Exception as e:
            logger.error(f"取得記憶體資訊失敗: {e}")
            return {
                'available': False,
                'error': str(e),
            }
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """
        取得 GPU 使用資訊
        
        Returns:
            GPU 資訊字典
        """
        if not TORCH_AVAILABLE:
            return {
                'available': False,
                'cuda_available': False,
                'error': 'torch 未安裝',
            }
        
        try:
            cuda_available = torch.cuda.is_available()
            
            if not cuda_available:
                return {
                    'available': False,
                    'cuda_available': False,
                    'reason': 'CUDA 不可用',
                }
            
            device_count = torch.cuda.device_count()
            devices = []
            
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                
                # 取得記憶體使用
                try:
                    torch.cuda.set_device(i)
                    allocated = torch.cuda.memory_allocated(i)
                    reserved = torch.cuda.memory_reserved(i)
                    total = props.total_memory
                except Exception:
                    allocated = 0
                    reserved = 0
                    total = props.total_memory
                
                devices.append({
                    'index': i,
                    'name': props.name,
                    'total_memory_bytes': total,
                    'total_memory_gb': round(total / (1024**3), 2),
                    'allocated_memory_bytes': allocated,
                    'allocated_memory_gb': round(allocated / (1024**3), 2),
                    'reserved_memory_bytes': reserved,
                    'reserved_memory_gb': round(reserved / (1024**3), 2),
                    'free_memory_bytes': total - allocated,
                    'free_memory_gb': round((total - allocated) / (1024**3), 2),
                    'memory_percent': round(allocated / total * 100, 2) if total > 0 else 0,
                    'compute_capability': f"{props.major}.{props.minor}",
                    'multi_processor_count': props.multi_processor_count,
                })
            
            return {
                'available': True,
                'cuda_available': True,
                'cuda_version': torch.version.cuda,
                'device_count': device_count,
                'current_device': torch.cuda.current_device(),
                'devices': devices,
            }
            
        except Exception as e:
            logger.error(f"取得 GPU 資訊失敗: {e}")
            return {
                'available': False,
                'cuda_available': False,
                'error': str(e),
            }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """
        取得磁碟使用資訊
        
        Returns:
            磁碟資訊字典
        """
        if not PSUTIL_AVAILABLE:
            return {
                'available': False,
                'error': 'psutil 未安裝',
            }
        
        try:
            # 取得當前工作目錄的磁碟
            disk = psutil.disk_usage(os.getcwd())
            
            return {
                'available': True,
                'total_bytes': disk.total,
                'total_gb': round(disk.total / (1024**3), 2),
                'used_bytes': disk.used,
                'used_gb': round(disk.used / (1024**3), 2),
                'free_bytes': disk.free,
                'free_gb': round(disk.free / (1024**3), 2),
                'percent': disk.percent,
            }
        except Exception as e:
            logger.error(f"取得磁碟資訊失敗: {e}")
            return {
                'available': False,
                'error': str(e),
            }
    
    def get_uptime(self) -> Dict[str, Any]:
        """
        取得系統與應用程式執行時間
        
        Returns:
            執行時間資訊字典
        """
        try:
            # 應用程式執行時間
            app_uptime_seconds = time.time() - self._start_time
            
            # 系統執行時間
            if PSUTIL_AVAILABLE:
                boot_time = psutil.boot_time()
                system_uptime_seconds = time.time() - boot_time
            else:
                system_uptime_seconds = None
            
            return {
                'app_uptime_seconds': int(app_uptime_seconds),
                'app_uptime_formatted': self._format_duration(app_uptime_seconds),
                'system_uptime_seconds': int(system_uptime_seconds) if system_uptime_seconds else None,
                'system_uptime_formatted': self._format_duration(system_uptime_seconds) if system_uptime_seconds else None,
                'app_start_time': datetime.fromtimestamp(self._start_time).isoformat(),
            }
        except Exception as e:
            logger.error(f"取得執行時間失敗: {e}")
            return {
                'error': str(e),
            }
    
    def get_full_status(self) -> Dict[str, Any]:
        """
        取得完整的系統狀態
        
        Returns:
            包含所有監控資訊的字典
        """
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'gpu': self.get_gpu_info(),
            'disk': self.get_disk_info(),
            'uptime': self.get_uptime(),
        }
    
    def get_health_check(self) -> Dict[str, Any]:
        """
        取得健康檢查結果
        
        Returns:
            健康檢查結果字典
        """
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        
        # 判斷健康狀態
        issues = []
        
        if cpu_info.get('available') and cpu_info.get('percent', 0) > 90:
            issues.append('CPU 使用率過高')
        
        if memory_info.get('available') and memory_info.get('percent', 0) > 90:
            issues.append('記憶體使用率過高')
        
        status = 'healthy' if not issues else 'warning'
        
        return {
            'status': status,
            'issues': issues,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'cpu_percent': cpu_info.get('percent'),
            'memory_percent': memory_info.get('percent'),
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        格式化時間長度
        
        Args:
            seconds: 秒數
            
        Returns:
            格式化的時間字串
        """
        if seconds is None:
            return '未知'
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} 天")
        if hours > 0:
            parts.append(f"{hours} 小時")
        if minutes > 0:
            parts.append(f"{minutes} 分鐘")
        if secs > 0 or not parts:
            parts.append(f"{secs} 秒")
        
        return ' '.join(parts)


# 全域服務實例
_monitor_service: Optional[MonitorService] = None


def get_monitor_service() -> MonitorService:
    """取得 MonitorService 實例"""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = MonitorService()
    return _monitor_service
