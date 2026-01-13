"""
多國語言翻譯系統 - 模型服務

本模組負責模型的載入與推論，支援多種模式：
- Local: 本地 Transformers 模型載入（GPU/CPU）
- Remote: 遠端 API 呼叫（OpenAI 相容 / HuggingFace Inference）
- 單例模式確保資源只初始化一次
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable

from django.conf import settings

from translator.enums import ExecutionMode, ModelStatus, QualityMode
from translator.errors import ErrorCode, TranslationError
from translator.utils.config_loader import ConfigLoader
from translator.services.model_providers import (
    BaseModelProvider,
    LocalModelProvider,
    RemoteAPIProvider,
)

logger = logging.getLogger('translator')


class ModelService:
    """
    模型服務（單例模式）
    
    負責模型的載入、管理與推論，支援本地與遠端模式
    """
    
    _instance: Optional['ModelService'] = None
    _lock = threading.Lock()
    
    # Provider 相關屬性
    _provider: Optional[BaseModelProvider] = None
    _provider_type: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'ModelService':
        """取得 ModelService 單例實例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_status(cls) -> str:
        """取得模型狀態"""
        if cls._provider is None:
            return ModelStatus.NOT_LOADED
        return cls._provider.get_status()
    
    @classmethod
    def get_execution_mode(cls) -> str:
        """取得執行模式（gpu/cpu/remote）"""
        if cls._provider is None:
            return ExecutionMode.CPU
        return cls._provider.get_execution_mode()
    
    @classmethod
    def is_loaded(cls) -> bool:
        """檢查模型是否已載入"""
        if cls._provider is None:
            return False
        return cls._provider.is_loaded()
    
    @classmethod
    def get_error_message(cls) -> Optional[str]:
        """取得錯誤訊息"""
        if cls._provider is None:
            return None
        return cls._provider.get_error_message()
    
    @classmethod
    def get_loading_progress(cls) -> float:
        """取得模型載入進度百分比 (0.0-100.0)"""
        if cls._provider is None:
            return 0.0
        return cls._provider.get_loading_progress()
    
    def set_progress_callback(self, callback: Optional[Callable[[float, str], None]]):
        """
        設定進度回呼函數（僅本地模式支援）
        
        Args:
            callback: 回呼函數 (進度百分比, 訊息)
        """
        if self._provider and hasattr(self._provider, 'set_progress_callback'):
            self._provider.set_progress_callback(callback)
    
    
    def load_model(self) -> bool:
        """
        載入模型（根據設定檔選擇 provider）
        
        Returns:
            bool: 載入是否成功
        """
        if self.is_loaded():
            logger.info("模型已載入，跳過重複載入")
            return True
        
        try:
            # 讀取設定檔，決定使用哪種 provider
            config = ConfigLoader.get_model_config()
            provider_config = config.get('provider', {})
            provider_type = provider_config.get('type', 'local')
            
            logger.info(f"準備載入模型（provider={provider_type}）...")
            
            # 建立對應的 provider
            if provider_type == 'local':
                self.__class__._provider = LocalModelProvider(provider_config)
                self.__class__._provider_type = 'local'
            elif provider_type == 'openai':
                self.__class__._provider = RemoteAPIProvider(provider_config, 'openai')
                self.__class__._provider_type = 'openai'
            elif provider_type == 'huggingface':
                self.__class__._provider = RemoteAPIProvider(provider_config, 'huggingface')
                self.__class__._provider_type = 'huggingface'
            else:
                logger.error(f"不支援的 provider 類型: {provider_type}")
                return False
            
            # 載入模型
            success = self._provider.load()
            
            if success:
                logger.info(f"✓ 模型載入成功（provider={provider_type}）")
                logger.info(f"  執行模式: {self.get_execution_mode()}")
            
            return success
            
        except Exception as e:
            logger.error(f"模型載入失敗: {e}", exc_info=True)
            return False
    
    
    def generate(
        self,
        prompt: str,
        quality: str = QualityMode.STANDARD,
        generation_overrides: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        執行文字生成
        
        Args:
            prompt: 輸入提示
            quality: 品質模式
            generation_overrides: 覆寫生成參數（選填）
            
        Returns:
            生成的文字
            
        Raises:
            TranslationError: 模型未載入或生成失敗
        """
        if not self.is_loaded():
            raise TranslationError(ErrorCode.MODEL_NOT_LOADED)
        
        try:
            # 取得生成參數
            gen_params = self._get_generation_params(quality)

            # 允許呼叫端覆寫參數
            if generation_overrides:
                gen_params = {**gen_params, **generation_overrides}
            
            # 委派給 provider
            return self._provider.generate(prompt, gen_params)
            
        except TranslationError:
            raise
        except Exception as e:
            logger.error(f"文字生成失敗: {e}", exc_info=True)
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"文字生成失敗: {str(e)}"
            )
    
    
    def _get_generation_params(self, quality: str) -> Dict[str, Any]:
        """
        取得生成參數
        
        Args:
            quality: 品質模式
            
        Returns:
            生成參數字典
        """
        config = ConfigLoader.get_model_config()
        generation_config = config.get('generation', {})
        
        # 預設參數
        defaults = {
            QualityMode.FAST: {
                'temperature': 0.7,
                'top_p': 0.9,
                'num_beams': 1,
                'do_sample': True,
                'min_new_tokens': 1,
                'max_new_tokens': 128,
                'max_tokens': 128,  # 用於遠端 API
                'repetition_penalty': 1.5,
                'no_repeat_ngram_size': 3,
            },
            QualityMode.STANDARD: {
                'temperature': 0.5,
                'top_p': 0.85,
                'num_beams': 1,
                'do_sample': True,
                'min_new_tokens': 1,
                'max_new_tokens': 256,
                'max_tokens': 256,
                'repetition_penalty': 1.5,
                'no_repeat_ngram_size': 3,
            },
            QualityMode.HIGH: {
                'temperature': 0.3,
                'top_p': 0.8,
                'num_beams': 4,
                'do_sample': False,
                'min_new_tokens': 1,
                'max_new_tokens': 512,
                'max_tokens': 512,
                'repetition_penalty': 1.5,
                'no_repeat_ngram_size': 3,
            },
        }
        
        # 從配置取得參數，若無則使用預設值
        quality_key = quality if quality in defaults else QualityMode.STANDARD
        params = generation_config.get(quality_key, defaults[quality_key])
        
        # 合併預設值與配置值
        result = {**defaults[quality_key]}
        result.update(params)
        
        # Local provider 專用邏輯
        num_beams = result.get('num_beams', 1)
        if num_beams and int(num_beams) > 1:
            result['do_sample'] = False  # beam search 時避免隨機採樣
        
        return result
    
    def unload_model(self):
        """卸載模型以釋放記憶體"""
        with self._lock:
            if self._provider is not None:
                self._provider.unload()
                self._provider = None
            
            self._provider_type = None
            logger.info("模型已卸載")


# 方便外部使用的函數
def get_model_service() -> ModelService:
    """取得 ModelService 單例實例"""
    return ModelService.get_instance()
