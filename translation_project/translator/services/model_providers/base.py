"""
多國語言翻譯系統 - 模型提供者基礎類別

定義所有模型提供者必須實作的介面
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseModelProvider(ABC):
    """
    模型提供者抽象基礎類別
    
    所有模型提供者（本地/遠端）都必須實作此介面
    """
    
    @abstractmethod
    def load(self) -> bool:
        """
        載入/初始化模型
        
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        generation_params: Dict[str, Any],
    ) -> str:
        """
        執行文字生成
        
        Args:
            prompt: 輸入提示
            generation_params: 生成參數
            
        Returns:
            生成的文字
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """
        檢查模型是否已載入/可用
        
        Returns:
            是否已載入
        """
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        """
        取得模型狀態
        
        Returns:
            狀態字串（not_loaded/loading/loaded/error）
        """
        pass
    
    @abstractmethod
    def get_execution_mode(self) -> str:
        """
        取得執行模式
        
        Returns:
            執行模式（gpu/cpu/remote）
        """
        pass
    
    @abstractmethod
    def unload(self):
        """卸載模型以釋放資源"""
        pass
    
    def get_error_message(self) -> Optional[str]:
        """
        取得錯誤訊息（若有）
        
        Returns:
            錯誤訊息或 None
        """
        return None
    
    def get_loading_progress(self) -> float:
        """
        取得載入進度百分比
        
        Returns:
            進度百分比（0.0-100.0）
        """
        return 0.0
