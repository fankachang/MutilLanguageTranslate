"""
多國語言翻譯系統 - API 序列化器

定義請求與回應的序列化/反序列化邏輯
"""

from typing import Any, Dict, List, Optional

from translator.enums import QualityMode
from translator.errors import ErrorCode, TranslationError
from translator.utils.config_loader import ConfigLoader


class TranslationRequestSerializer:
    """
    翻譯請求序列化器
    
    負責驗證與解析翻譯請求資料
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self._errors: List[Dict[str, str]] = []
        self._validated_data: Optional[Dict[str, Any]] = None
    
    def is_valid(self) -> bool:
        """
        驗證請求資料
        
        Returns:
            是否通過驗證
        """
        self._errors = []
        self._validated_data = {}
        
        # 驗證 text
        text = self.data.get('text', '')
        if not text or not str(text).strip():
            self._errors.append({
                'field': 'text',
                'code': ErrorCode.VALIDATION_EMPTY_TEXT,
                'message': '請輸入要翻譯的文字',
            })
        else:
            text = str(text)
            max_length = ConfigLoader.get_max_text_length()
            if len(text) > max_length:
                self._errors.append({
                    'field': 'text',
                    'code': ErrorCode.VALIDATION_TEXT_TOO_LONG,
                    'message': f'文字長度超過 {max_length} 字元，請縮短後再試',
                })
            else:
                self._validated_data['text'] = text
        
        # 驗證 source_language
        source_language = self.data.get('source_language', 'auto')
        if not ConfigLoader.is_valid_language_code(source_language):
            self._errors.append({
                'field': 'source_language',
                'code': ErrorCode.VALIDATION_INVALID_LANGUAGE,
                'message': f'無效的來源語言代碼: {source_language}',
            })
        else:
            self._validated_data['source_language'] = source_language
        
        # 驗證 target_language
        target_language = self.data.get('target_language')
        if not target_language:
            self._errors.append({
                'field': 'target_language',
                'code': ErrorCode.VALIDATION_INVALID_LANGUAGE,
                'message': '缺少目標語言參數',
            })
        elif target_language == 'auto':
            self._errors.append({
                'field': 'target_language',
                'code': ErrorCode.VALIDATION_INVALID_LANGUAGE,
                'message': '目標語言不可為自動偵測',
            })
        elif not ConfigLoader.is_valid_language_code(target_language):
            self._errors.append({
                'field': 'target_language',
                'code': ErrorCode.VALIDATION_INVALID_LANGUAGE,
                'message': f'無效的目標語言代碼: {target_language}',
            })
        else:
            self._validated_data['target_language'] = target_language
        
        # 驗證 quality
        quality = self.data.get('quality', QualityMode.STANDARD)
        if not QualityMode.is_valid(quality):
            quality = QualityMode.STANDARD
        self._validated_data['quality'] = quality
        
        # 驗證來源與目標不同
        if (self._validated_data.get('source_language') and 
            self._validated_data.get('target_language') and
            self._validated_data['source_language'] != 'auto' and
            self._validated_data['source_language'] == self._validated_data['target_language']):
            self._errors.append({
                'field': 'target_language',
                'code': ErrorCode.VALIDATION_SAME_LANGUAGE,
                'message': '來源語言與目標語言不可相同',
            })
        
        return len(self._errors) == 0
    
    @property
    def errors(self) -> List[Dict[str, str]]:
        """取得驗證錯誤列表"""
        return self._errors
    
    @property
    def validated_data(self) -> Dict[str, Any]:
        """取得驗證後的資料"""
        if self._validated_data is None:
            raise ValueError("請先呼叫 is_valid() 進行驗證")
        return self._validated_data
    
    def get_first_error(self) -> Optional[Dict[str, str]]:
        """取得第一個錯誤"""
        return self._errors[0] if self._errors else None


class TranslationResponseSerializer:
    """
    翻譯回應序列化器
    
    負責將翻譯結果序列化為 API 回應格式
    """
    
    @staticmethod
    def serialize_success(
        request_id: str,
        translated_text: str,
        processing_time_ms: int,
        execution_mode: str,
        detected_language: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        序列化成功回應
        
        Args:
            request_id: 請求 ID
            translated_text: 翻譯結果
            processing_time_ms: 處理時間
            execution_mode: 執行模式
            detected_language: 偵測到的語言
            confidence_score: 信心分數
            
        Returns:
            API 回應字典
        """
        result = {
            'request_id': request_id,
            'status': 'completed',
            'translated_text': translated_text,
            'processing_time_ms': processing_time_ms,
            'execution_mode': execution_mode,
        }
        
        if detected_language:
            result['detected_language'] = detected_language
        
        if confidence_score is not None:
            result['confidence_score'] = confidence_score
        
        return result
    
    @staticmethod
    def serialize_queued(
        request_id: str,
        queue_position: int,
        estimated_wait_seconds: int,
    ) -> Dict[str, Any]:
        """
        序列化排隊回應
        
        Args:
            request_id: 請求 ID
            queue_position: 佇列位置
            estimated_wait_seconds: 預估等待時間
            
        Returns:
            API 回應字典
        """
        return {
            'request_id': request_id,
            'status': 'queued',
            'queue_position': queue_position,
            'estimated_wait_seconds': estimated_wait_seconds,
        }
    
    @staticmethod
    def serialize_error(
        request_id: str,
        error_code: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """
        序列化錯誤回應
        
        Args:
            request_id: 請求 ID
            error_code: 錯誤代碼
            error_message: 錯誤訊息
            
        Returns:
            API 回應字典
        """
        return {
            'request_id': request_id,
            'status': 'failed',
            'error': {
                'code': error_code,
                'message': error_message,
            },
        }


class LanguageListSerializer:
    """
    語言列表序列化器
    """
    
    @staticmethod
    def serialize(languages: list) -> Dict[str, Any]:
        """
        序列化語言列表
        
        Args:
            languages: Language 物件列表
            
        Returns:
            API 回應字典
        """
        return {
            'languages': [
                {
                    'code': lang.code,
                    'name': lang.name,
                    'name_en': lang.name_en,
                    'is_enabled': lang.is_enabled,
                }
                for lang in languages
            ],
            'default_source_language': ConfigLoader.get_default_source_language(),
            'default_target_language': ConfigLoader.get_default_target_language(),
        }
