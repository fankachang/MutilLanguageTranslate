"""
多國語言翻譯系統 - 本地模型提供者

使用 Transformers 在本地載入與推論模型
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import torch
from django.conf import settings

from translator.enums import ExecutionMode, ModelStatus
from translator.errors import ErrorCode, TranslationError
from .base import BaseModelProvider

logger = logging.getLogger('translator')


class LocalModelProvider(BaseModelProvider):
    """
    本地模型提供者
    
    使用 Transformers 載入模型到本地記憶體（GPU/CPU）進行推論
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地模型提供者
        
        Args:
            config: 模型配置
        """
        self._config = config
        self._model = None
        self._tokenizer = None
        self._device: Optional[str] = None
        self._status: str = ModelStatus.NOT_LOADED
        self._error_message: Optional[str] = None
        self._loading_progress: float = 0.0
        self._progress_callback: Optional[Callable[[float, str], None]] = None
    
    def set_progress_callback(self, callback: Optional[Callable[[float, str], None]]):
        """設定進度回呼函數"""
        self._progress_callback = callback
    
    def load(self) -> bool:
        """載入模型到本地記憶體"""
        if self._status == ModelStatus.LOADED:
            logger.info("模型已載入，跳過重複載入")
            return True
        
        if self._status == ModelStatus.LOADING:
            logger.warning("模型正在載入中")
            return False
        
        self._status = ModelStatus.LOADING
        self._loading_progress = 0.0
        logger.info("開始載入 TAIDE-LX-7B 模型（本地模式）...")
        self._report_progress(5, "初始化配置...")
        
        try:
            # 取得模型路徑
            model_path = self._get_model_path()
            self._report_progress(10, f"尋找模型: {model_path}")

            if not model_path.exists():
                raise FileNotFoundError(f"模型路徑不存在: {model_path}")

            # 延遲導入 transformers
            self._report_progress(15, "導入 transformers 套件...")
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # 讀取量化與 offload 選項
            local_config = self._config.get('local', {})
            quant_cfg = local_config.get('quantization', {}) or {}
            enable_4bit_config = bool(quant_cfg.get('enable_4bit', False)) and bool(quant_cfg.get('load_in_4bit', False))
            offload_cfg = quant_cfg.get('offload', {}) or {}

            # 偵測 GPU 可用性
            force_cpu = local_config.get('force_cpu', False)

            if torch.cuda.is_available() and not force_cpu:
                self._device = ExecutionMode.GPU
                
                # 取得 GPU VRAM 大小
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                logger.info(f"偵測到 CUDA GPU: {torch.cuda.get_device_name(0)}, VRAM: {gpu_memory_gb:.2f} GB")
                
                # 自動決定是否使用 4-bit 量化
                auto_enable_4bit = gpu_memory_gb <= 12.0
                enable_4bit = enable_4bit_config if 'enable_4bit' in quant_cfg else auto_enable_4bit
                
                if enable_4bit:
                    logger.info("GPU VRAM ≤ 12GB，啟用 4-bit 量化以節省記憶體")
                else:
                    logger.info("GPU VRAM > 12GB，使用 float16 模式")
                
                self._report_progress(20, "使用 GPU 模式，載入模型...")

                max_gpu_memory = local_config.get('max_gpu_memory')
                device_map_config = offload_cfg.get('device_map', 'auto')

                if max_gpu_memory:
                    max_memory = {0: f"{max_gpu_memory}GiB"}
                else:
                    max_memory = None

                # 嘗試 4-bit 量化
                if enable_4bit:
                    try:
                        import bitsandbytes as bnb  # noqa: F401
                        from transformers import BitsAndBytesConfig
                        
                        logger.info("嘗試以 4-bit 量化載入模型 (bitsandbytes)...")
                        self._report_progress(25, "4-bit 量化載入中...")
                        
                        bnb_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4"
                        )
                        
                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            quantization_config=bnb_config,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                        logger.info("✓ 成功使用 4-bit 量化載入模型")
                    except ImportError:
                        logger.warning("bitsandbytes 未安裝，改回 float16 模式")
                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            dtype=torch.float16,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                    except Exception as e:
                        logger.warning(f"4-bit 量化載入失敗，改回非量化載入: {e}")
                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            dtype=torch.float16,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                else:
                    # float16 模式
                    self._report_progress(25, "float16 模式載入中...")
                    self._model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        dtype=torch.float16,
                        device_map=device_map_config,
                        max_memory=max_memory,
                        trust_remote_code=True,
                    )
            else:
                self._device = ExecutionMode.CPU
                logger.info("使用 CPU 模式")
                self._report_progress(20, "使用 CPU 模式，載入模型...")

                self._model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                )

            # 載入 tokenizer
            self._report_progress(75, "載入 Tokenizer...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True,
            )

            self._report_progress(95, "模型初始化中...")
            self._status = ModelStatus.LOADED
            self._loading_progress = 100.0
            self._error_message = None
            logger.info(f"模型載入成功，執行模式: {self._device}")
            self._report_progress(100, "模型載入完成！")
            return True

        except Exception as e:
            self._status = ModelStatus.ERROR
            self._error_message = str(e)
            self._loading_progress = 0.0
            logger.error(f"模型載入失敗: {e}", exc_info=True)
            self._report_progress(0, f"模型載入失敗: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        generation_params: Dict[str, Any],
    ) -> str:
        """執行文字生成"""
        if not self.is_loaded():
            raise TranslationError(ErrorCode.MODEL_NOT_LOADED)
        
        try:
            # 編碼輸入
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
            )

            # 移除尾端可能的 eos_token
            input_ids = inputs.get('input_ids')
            attention_mask = inputs.get('attention_mask')
            eos_id = self._tokenizer.eos_token_id
            if input_ids is not None and eos_id is not None and input_ids.shape[-1] > 0:
                if int(input_ids[0, -1]) == int(eos_id):
                    inputs['input_ids'] = input_ids[:, :-1]
                    if attention_mask is not None and attention_mask.shape[-1] == input_ids.shape[-1]:
                        inputs['attention_mask'] = attention_mask[:, :-1]
            
            # 移動到正確的設備
            if self._device == ExecutionMode.GPU:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 執行生成
            with torch.no_grad():
                from transformers import GenerationConfig

                generation_config = GenerationConfig(**generation_params)

                generate_kwargs = {
                    **inputs,
                    'generation_config': generation_config,
                    'pad_token_id': self._tokenizer.eos_token_id,
                    'eos_token_id': self._tokenizer.eos_token_id,
                }

                if 'early_stopping' not in generate_kwargs and generation_params.get('num_beams', 1) > 1:
                    generate_kwargs['early_stopping'] = True
                
                outputs = self._model.generate(**generate_kwargs)
            
            # 只解碼新生成的 token
            prompt_len = int(inputs['input_ids'].shape[-1])
            generated_ids = outputs[0][prompt_len:]
            generated_text = self._tokenizer.decode(
                generated_ids,
                skip_special_tokens=True,
            ).strip()

            logger.debug(
                "generate() 完成（本地模式）| new_tokens=%d | preview=%r",
                int(generated_ids.shape[-1]) if hasattr(generated_ids, 'shape') else -1,
                generated_text[:200],
            )
            
            return generated_text
            
        except Exception as e:
            logger.error(f"文字生成失敗: {e}", exc_info=True)
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"文字生成失敗: {str(e)}"
            )
    
    def is_loaded(self) -> bool:
        """檢查模型是否已載入"""
        return self._status == ModelStatus.LOADED
    
    def get_status(self) -> str:
        """取得模型狀態"""
        return self._status
    
    def get_execution_mode(self) -> str:
        """取得執行模式"""
        return self._device or ExecutionMode.CPU
    
    def get_error_message(self) -> Optional[str]:
        """取得錯誤訊息"""
        return self._error_message
    
    def get_loading_progress(self) -> float:
        """取得載入進度"""
        return self._loading_progress
    
    def unload(self):
        """卸載模型"""
        if self._model is not None:
            del self._model
            self._model = None
        
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self._status = ModelStatus.NOT_LOADED
        self._device = None
        logger.info("模型已卸載（本地模式）")
    
    def _report_progress(self, progress: float, message: str):
        """回報載入進度"""
        self._loading_progress = progress
        logger.info(f"模型載入進度: {progress:.1f}% - {message}")
        
        if self._progress_callback:
            try:
                self._progress_callback(progress, message)
            except Exception as e:
                logger.error(f"進度回呼執行失敗: {e}")
    
    def _get_model_path(self) -> Path:
        """取得模型路徑"""
        local_config = self._config.get('local', {})
        model_rel_path = local_config.get(
            'path',
            'models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979'
        )
        
        project_root = settings.PROJECT_ROOT
        return project_root / model_rel_path
