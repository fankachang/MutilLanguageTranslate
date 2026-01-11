"""
多國語言翻譯系統 - 模型服務

本模組負責 TAIDE-LX-7B 模型的載入與推論：
- 單例模式確保模型只載入一次
- GPU/CPU 自動偵測與切換
- 生成參數依品質模式配置
- 載入失敗時的錯誤處理
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any

import torch
from django.conf import settings

from translator.enums import ExecutionMode, ModelStatus, QualityMode
from translator.errors import ErrorCode, TranslationError
from translator.utils.config_loader import ConfigLoader

logger = logging.getLogger('translator')


class ModelService:
    """
    TAIDE-LX-7B 模型服務
    
    單例模式實現，負責模型的載入、管理與推論。
    """
    
    _instance: Optional['ModelService'] = None
    _lock = threading.Lock()
    
    # 模型相關屬性
    _model = None
    _tokenizer = None
    _device: str = None
    _status: str = ModelStatus.NOT_LOADED
    _error_message: Optional[str] = None
    
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
        return cls._status
    
    @classmethod
    def get_execution_mode(cls) -> str:
        """取得執行模式（GPU/CPU）"""
        return cls._device or ExecutionMode.CPU
    
    @classmethod
    def is_loaded(cls) -> bool:
        """檢查模型是否已載入"""
        return cls._status == ModelStatus.LOADED
    
    @classmethod
    def get_error_message(cls) -> Optional[str]:
        """取得錯誤訊息"""
        return cls._error_message
    
    def load_model(self) -> bool:
        """
        載入模型
        
        Returns:
            bool: 載入是否成功
        """
        if self._status == ModelStatus.LOADED:
            logger.info("模型已載入，跳過重複載入")
            return True
        
        if self._status == ModelStatus.LOADING:
            logger.warning("模型正在載入中")
            return False
        
        self._status = ModelStatus.LOADING
        logger.info("開始載入 TAIDE-LX-7B 模型...")
        
        try:
            # 載入配置
            config = ConfigLoader.get_model_config()
            model_path = self._get_model_path(config)
            
            if not model_path.exists():
                raise FileNotFoundError(f"模型路徑不存在: {model_path}")
            
            # 延遲導入 transformers 以加快啟動速度
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # 偵測 GPU 可用性
            force_cpu = config.get('model', {}).get('force_cpu', False)
            
            if torch.cuda.is_available() and not force_cpu:
                self._device = ExecutionMode.GPU
                logger.info("偵測到 CUDA GPU，使用 GPU 模式")
                
                max_gpu_memory = config.get('model', {}).get('max_gpu_memory')
                device_map_config = "auto"
                
                if max_gpu_memory:
                    # 指定 GPU 記憶體上限
                    max_memory = {0: f"{max_gpu_memory}GiB"}
                else:
                    max_memory = None
                
                self._model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    torch_dtype=torch.float16,
                    device_map=device_map_config,
                    max_memory=max_memory,
                    trust_remote_code=True,
                )
            else:
                self._device = ExecutionMode.CPU
                logger.info("使用 CPU 模式")
                
                self._model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                )
            
            # 載入 tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True,
            )
            
            self._status = ModelStatus.LOADED
            self._error_message = None
            logger.info(f"模型載入成功，執行模式: {self._device}")
            return True
            
        except Exception as e:
            self._status = ModelStatus.ERROR
            self._error_message = str(e)
            logger.error(f"模型載入失敗: {e}", exc_info=True)
            return False
    
    def _get_model_path(self, config: Dict[str, Any]) -> Path:
        """
        取得模型路徑
        
        Args:
            config: 模型配置
            
        Returns:
            模型路徑
        """
        model_rel_path = config.get('model', {}).get(
            'path',
            'models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979'
        )
        
        # 從專案根目錄開始解析
        project_root = settings.PROJECT_ROOT
        return project_root / model_rel_path
    
    def generate(
        self,
        prompt: str,
        quality: str = QualityMode.STANDARD,
    ) -> str:
        """
        執行文字生成
        
        Args:
            prompt: 輸入提示
            quality: 品質模式
            
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
            
            # 編碼輸入
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
            )
            
            # 移動到正確的設備
            if self._device == ExecutionMode.GPU:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 執行生成
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    **gen_params,
                    pad_token_id=self._tokenizer.eos_token_id,
                    do_sample=True,
                )
            
            # 解碼輸出
            generated_text = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
            )
            
            # 移除輸入部分，只保留生成的內容
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
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
                'max_new_tokens': 512,
            },
            QualityMode.STANDARD: {
                'temperature': 0.5,
                'top_p': 0.85,
                'num_beams': 2,
                'max_new_tokens': 1024,
            },
            QualityMode.HIGH: {
                'temperature': 0.3,
                'top_p': 0.8,
                'num_beams': 4,
                'max_new_tokens': 2048,
            },
        }
        
        # 從配置取得參數，若無則使用預設值
        quality_key = quality if quality in defaults else QualityMode.STANDARD
        params = generation_config.get(quality_key, defaults[quality_key])
        
        return {
            'temperature': params.get('temperature', defaults[quality_key]['temperature']),
            'top_p': params.get('top_p', defaults[quality_key]['top_p']),
            'num_beams': params.get('num_beams', defaults[quality_key]['num_beams']),
            'max_new_tokens': params.get('max_new_tokens', defaults[quality_key]['max_new_tokens']),
        }
    
    def unload_model(self):
        """卸載模型以釋放記憶體"""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
            
            if self._tokenizer is not None:
                del self._tokenizer
                self._tokenizer = None
            
            # 清理 GPU 記憶體
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._status = ModelStatus.NOT_LOADED
            self._device = None
            logger.info("模型已卸載")


# 方便外部使用的函數
def get_model_service() -> ModelService:
    """取得 ModelService 單例實例"""
    return ModelService.get_instance()
