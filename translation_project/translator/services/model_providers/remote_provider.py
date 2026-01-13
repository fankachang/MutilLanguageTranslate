"""
多國語言翻譯系統 - 遠端 API 模型提供者

透過 HTTP API 呼叫遠端推論服務（OpenAI 相容 / Hugging Face Inference）
"""

import logging
from typing import Dict, Any, Optional

import httpx

from translator.enums import ModelStatus
from translator.errors import ErrorCode, TranslationError
from .base import BaseModelProvider

logger = logging.getLogger('translator')


class RemoteAPIProvider(BaseModelProvider):
    """
    遠端 API 模型提供者
    
    支援：
    - OpenAI 相容 API（vLLM、Ollama、OpenAI、LM Studio 等）
    - Hugging Face Inference Endpoint
    """
    
    def __init__(self, config: Dict[str, Any], provider_type: str):
        """
        初始化遠端 API 提供者
        
        Args:
            config: 模型配置
            provider_type: 提供者類型（'openai' 或 'huggingface'）
        """
        self._config = config
        self._provider_type = provider_type
        self._status: str = ModelStatus.NOT_LOADED
        self._error_message: Optional[str] = None
        self._client: Optional[httpx.Client] = None
        
        # 取得對應的配置
        if provider_type == 'openai':
            self._api_config = config.get('openai', {})
            self._api_base = self._api_config.get('api_base', 'http://localhost:8000/v1')
            self._api_key = self._api_config.get('api_key')
            self._model_name = self._api_config.get('model', 'taide/TAIDE-LX-7B')
        elif provider_type == 'huggingface':
            self._api_config = config.get('huggingface', {})
            self._api_base = self._api_config.get('endpoint_url', '')
            self._api_key = self._api_config.get('api_token')
            self._model_name = None  # HF Inference 不需要 model 欄位
        else:
            raise ValueError(f"不支援的 provider 類型: {provider_type}")
        
        self._timeout = self._api_config.get('timeout', 120)
        self._max_retries = self._api_config.get('max_retries', 2)
    
    def load(self) -> bool:
        """初始化 HTTP 客戶端與測試連線"""
        if self._status == ModelStatus.LOADED:
            logger.info("遠端 API 已初始化")
            return True
        
        try:
            logger.info(f"初始化遠端 API 客戶端（{self._provider_type}）...")
            
            # 建立 HTTP 客戶端
            headers = {}
            if self._api_key:
                if self._provider_type == 'openai':
                    headers['Authorization'] = f'Bearer {self._api_key}'
                elif self._provider_type == 'huggingface':
                    headers['Authorization'] = f'Bearer {self._api_key}'
            
            self._client = httpx.Client(
                base_url=self._api_base,
                headers=headers,
                timeout=httpx.Timeout(self._timeout),
            )
            
            # 簡單的健康檢查（選填，某些服務可能沒有健康檢查端點）
            # 這裡先標記為已載入，實際連線會在首次 generate() 時驗證
            self._status = ModelStatus.LOADED
            self._error_message = None
            logger.info(f"✓ 遠端 API 客戶端初始化成功（{self._provider_type}）")
            logger.info(f"  API Base: {self._api_base}")
            logger.info(f"  Model: {self._model_name or 'N/A (Inference Endpoint)'}")
            return True
            
        except Exception as e:
            self._status = ModelStatus.ERROR
            self._error_message = str(e)
            logger.error(f"遠端 API 客戶端初始化失敗: {e}", exc_info=True)
            return False
    
    def generate(
        self,
        prompt: str,
        generation_params: Dict[str, Any],
    ) -> str:
        """透過 API 執行文字生成"""
        if not self.is_loaded():
            raise TranslationError(ErrorCode.MODEL_NOT_LOADED)
        
        try:
            if self._provider_type == 'openai':
                return self._generate_openai(prompt, generation_params)
            elif self._provider_type == 'huggingface':
                return self._generate_huggingface(prompt, generation_params)
            else:
                raise ValueError(f"不支援的 provider 類型: {self._provider_type}")
                
        except httpx.TimeoutException as e:
            logger.error(f"API 請求逾時: {e}")
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"遠端 API 請求逾時: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"API 請求失敗: {e.response.status_code} - {e.response.text}")
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"遠端 API 請求失敗: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"文字生成失敗: {e}", exc_info=True)
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"文字生成失敗: {str(e)}"
            )
    
    def _generate_openai(self, prompt: str, generation_params: Dict[str, Any]) -> str:
        """使用 OpenAI 相容 API 生成文字"""
        # 轉換參數名稱（Transformers → OpenAI API）
        api_params = {
            'model': self._model_name,
            'prompt': prompt,
            'max_tokens': generation_params.get('max_new_tokens', generation_params.get('max_tokens', 512)),
            'temperature': generation_params.get('temperature', 0.7),
            'top_p': generation_params.get('top_p', 0.9),
            'n': 1,
            'stream': False,
        }
        
        # 移除 None 值
        api_params = {k: v for k, v in api_params.items() if v is not None}
        
        logger.debug(f"發送 OpenAI API 請求: {api_params}")
        
        response = self._client.post(
            '/completions',
            json=api_params,
        )
        response.raise_for_status()
        
        result = response.json()
        generated_text = result['choices'][0]['text'].strip()
        
        logger.debug(
            "generate() 完成（OpenAI API）| preview=%r",
            generated_text[:200],
        )
        
        return generated_text
    
    def _generate_huggingface(self, prompt: str, generation_params: Dict[str, Any]) -> str:
        """使用 Hugging Face Inference Endpoint 生成文字"""
        # HF Inference API 參數格式
        api_params = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': generation_params.get('max_new_tokens', generation_params.get('max_tokens', 512)),
                'temperature': generation_params.get('temperature', 0.7),
                'top_p': generation_params.get('top_p', 0.9),
                'do_sample': generation_params.get('do_sample', True),
                'return_full_text': False,  # 只回傳新生成的文字
            }
        }
        
        # 可選參數
        if 'num_beams' in generation_params:
            api_params['parameters']['num_beams'] = generation_params['num_beams']
        if 'repetition_penalty' in generation_params:
            api_params['parameters']['repetition_penalty'] = generation_params['repetition_penalty']
        
        logger.debug(f"發送 HuggingFace API 請求: {api_params}")
        
        response = self._client.post(
            '',  # Inference Endpoint 直接 POST 到根路徑
            json=api_params,
        )
        response.raise_for_status()
        
        result = response.json()
        
        # HF Inference 回應格式：[{"generated_text": "..."}]
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get('generated_text', '').strip()
        else:
            generated_text = result.get('generated_text', '').strip()
        
        logger.debug(
            "generate() 完成（HuggingFace Inference）| preview=%r",
            generated_text[:200],
        )
        
        return generated_text
    
    def is_loaded(self) -> bool:
        """檢查 API 客戶端是否已初始化"""
        return self._status == ModelStatus.LOADED and self._client is not None
    
    def get_status(self) -> str:
        """取得狀態"""
        return self._status
    
    def get_execution_mode(self) -> str:
        """取得執行模式（遠端 API 固定回傳 'remote'）"""
        return 'remote'
    
    def get_error_message(self) -> Optional[str]:
        """取得錯誤訊息"""
        return self._error_message
    
    def unload(self):
        """關閉 HTTP 客戶端"""
        if self._client is not None:
            self._client.close()
            self._client = None
        
        self._status = ModelStatus.NOT_LOADED
        logger.info(f"遠端 API 客戶端已關閉（{self._provider_type}）")
