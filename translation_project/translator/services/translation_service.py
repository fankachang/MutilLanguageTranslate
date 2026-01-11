"""
多國語言翻譯系統 - 翻譯服務

本模組負責核心翻譯功能：
- Prompt 組裝
- 模型呼叫
- 結果解析
- 換行格式保留（FR-006）
- Prompt 注入防護（FR-038）
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

from translator.enums import ExecutionMode, QualityMode, TranslationStatus
from translator.errors import ErrorCode, TranslationError
from translator.models import TranslationRequest, TranslationResponse
from translator.services.model_service import ModelService, get_model_service
from translator.services.queue_service import QueueService, get_queue_service
from translator.services.statistics_service import StatisticsService, get_statistics_service
from translator.utils.config_loader import ConfigLoader

logger = logging.getLogger('translator')
translation_logger = logging.getLogger('translator.translation')


class TranslationService:
    """
    翻譯服務
    
    負責執行翻譯請求的核心處理邏輯。
    """
    
    # 語言代碼到中文名稱的映射
    LANGUAGE_NAMES = {
        'zh-TW': '繁體中文',
        'zh-CN': '簡體中文',
        'en': '英文',
        'ja': '日文',
        'ko': '韓文',
        'fr': '法文',
        'de': '德文',
        'es': '西班牙文',
        'auto': '自動偵測',
    }
    
    def __init__(self):
        self._model_service = get_model_service()
        self._queue_service = get_queue_service()
        self._statistics_service = get_statistics_service()
    
    def translate(
        self,
        request: TranslationRequest
    ) -> TranslationResponse:
        """
        執行翻譯
        
        Args:
            request: 翻譯請求
            
        Returns:
            TranslationResponse 翻譯結果
        """
        start_time = time.time()
        
        try:
            # 驗證請求
            self._validate_request(request)
            
            # 檢查模型狀態
            if not self._model_service.is_loaded():
                # 嘗試載入模型
                if not self._model_service.load_model():
                    raise TranslationError(ErrorCode.MODEL_NOT_LOADED)
            
            # 嘗試取得處理槽位
            _, slot_result = self._queue_service.acquire_slot(request)
            
            if slot_result['status'] == TranslationStatus.REJECTED:
                return self._create_error_response(
                    request,
                    ErrorCode.QUEUE_FULL,
                    start_time
                )
            
            # 如果需要排隊，返回排隊狀態
            if slot_result['status'] == TranslationStatus.PENDING:
                return TranslationResponse(
                    request_id=request.request_id,
                    status=TranslationStatus.PENDING,
                    processing_time_ms=0,
                    execution_mode=self._model_service.get_execution_mode(),
                )
            
            # 執行翻譯
            try:
                result = self._perform_translation(request)
                
                # 記錄統計
                processing_time_ms = int((time.time() - start_time) * 1000)
                self._statistics_service.record_request(
                    success=True,
                    processing_time_ms=processing_time_ms,
                )
                
                # 記錄翻譯日誌
                translation_logger.info(
                    f"翻譯成功 | ID={request.request_id} | "
                    f"來源={request.source_language} | 目標={request.target_language} | "
                    f"字數={len(request.text)} | 時間={processing_time_ms}ms"
                )
                
                return TranslationResponse(
                    request_id=request.request_id,
                    status=TranslationStatus.COMPLETED,
                    processing_time_ms=processing_time_ms,
                    execution_mode=self._model_service.get_execution_mode(),
                    translated_text=result['translated_text'],
                    detected_language=result.get('detected_language'),
                    confidence_score=result.get('confidence_score'),
                )
                
            finally:
                # 釋放槽位
                self._queue_service.release_slot(request.request_id)
                
        except TranslationError as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            self._statistics_service.record_request(
                success=False,
                processing_time_ms=processing_time_ms,
            )
            
            logger.warning(
                f"翻譯失敗 | ID={request.request_id} | "
                f"錯誤={e.code}"
            )
            
            return self._create_error_response(request, e.code, start_time, e.message)
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            self._statistics_service.record_request(
                success=False,
                processing_time_ms=processing_time_ms,
            )
            
            logger.error(
                f"翻譯發生未預期錯誤 | ID={request.request_id} | "
                f"錯誤={str(e)}",
                exc_info=True
            )
            
            return self._create_error_response(
                request,
                ErrorCode.INTERNAL_ERROR,
                start_time,
                str(e)
            )
    
    def _validate_request(self, request: TranslationRequest):
        """
        驗證翻譯請求
        
        Args:
            request: 翻譯請求
            
        Raises:
            TranslationError: 驗證失敗
        """
        # 檢查文字是否為空
        if not request.text or not request.text.strip():
            raise TranslationError(ErrorCode.VALIDATION_EMPTY_TEXT)
        
        # 檢查文字長度
        max_length = ConfigLoader.get_max_text_length()
        if len(request.text) > max_length:
            raise TranslationError(ErrorCode.VALIDATION_TEXT_TOO_LONG)
        
        # 檢查語言代碼是否有效
        if not ConfigLoader.is_valid_language_code(request.source_language):
            raise TranslationError(ErrorCode.VALIDATION_INVALID_LANGUAGE)
        
        if not ConfigLoader.is_valid_language_code(request.target_language):
            raise TranslationError(ErrorCode.VALIDATION_INVALID_LANGUAGE)
        
        # 不能是 "auto" 目標語言
        if request.target_language == "auto":
            raise TranslationError(ErrorCode.VALIDATION_INVALID_LANGUAGE)
        
        # 來源與目標不可相同（除非來源是 auto）
        if (request.source_language != "auto" and 
            request.source_language == request.target_language):
            raise TranslationError(ErrorCode.VALIDATION_SAME_LANGUAGE)
    
    def _perform_translation(
        self,
        request: TranslationRequest
    ) -> Dict[str, Any]:
        """
        執行實際的翻譯
        
        Args:
            request: 翻譯請求
            
        Returns:
            包含翻譯結果的字典
        """
        detected_language = None
        confidence_score = None
        
        # 如果需要自動偵測語言
        source_lang = request.source_language
        if source_lang == "auto":
            detected_language, confidence_score = self._detect_language(request.text)
            source_lang = detected_language or "zh-TW"  # 預設繁體中文
        
        # 檢查偵測後的語言是否與目標相同
        if source_lang == request.target_language:
            raise TranslationError(ErrorCode.VALIDATION_SAME_LANGUAGE)
        
        # 組裝翻譯 Prompt
        prompt = self._build_translation_prompt(
            text=request.text,
            source_language=source_lang,
            target_language=request.target_language,
        )
        
        # 呼叫模型
        translated_text = self._model_service.generate(
            prompt=prompt,
            quality=request.quality,
        )
        
        # 清理輸出
        translated_text = self._clean_output(translated_text)
        
        return {
            'translated_text': translated_text,
            'detected_language': detected_language,
            'confidence_score': confidence_score,
        }
    
    def _detect_language(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        偵測文字語言
        
        Args:
            text: 待偵測文字
            
        Returns:
            (語言代碼, 信心分數) 或 (None, None)
        """
        try:
            # 取樣文字（最多 200 字）
            sample_text = text[:200] if len(text) > 200 else text
            
            # 組裝語言偵測 Prompt
            prompt = ConfigLoader.get_prompt_template('language_detection').format(
                text=self._sanitize_text(sample_text)
            )
            
            # 呼叫模型
            result = self._model_service.generate(
                prompt=prompt,
                quality=QualityMode.FAST,  # 語言偵測使用快速模式
            )
            
            # 解析結果（格式：語言代碼:信心分數）
            result = result.strip()
            if ':' in result:
                parts = result.split(':')
                lang_code = parts[0].strip()
                try:
                    confidence = float(parts[1].strip())
                except (ValueError, IndexError):
                    confidence = 0.8
                
                # 驗證語言代碼
                if ConfigLoader.is_valid_language_code(lang_code) and lang_code != "auto":
                    return lang_code, min(1.0, max(0.0, confidence))
            
            # 簡單的規則偵測作為回退
            return self._rule_based_detection(text)
            
        except Exception as e:
            logger.warning(f"語言偵測失敗: {e}")
            return self._rule_based_detection(text)
    
    def _rule_based_detection(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """
        基於規則的語言偵測（回退方案）
        
        Args:
            text: 待偵測文字
            
        Returns:
            (語言代碼, 信心分數)
        """
        # 簡單的字元範圍檢測
        sample = text[:500]
        
        # 統計各種字元類型
        cjk_count = len(re.findall(r'[\u4e00-\u9fff]', sample))
        hiragana_count = len(re.findall(r'[\u3040-\u309f]', sample))
        katakana_count = len(re.findall(r'[\u30a0-\u30ff]', sample))
        hangul_count = len(re.findall(r'[\uac00-\ud7af]', sample))
        latin_count = len(re.findall(r'[a-zA-Z]', sample))
        
        total = len(sample)
        if total == 0:
            return None, None
        
        # 判斷語言
        if (hiragana_count + katakana_count) / total > 0.1:
            return 'ja', 0.7
        elif hangul_count / total > 0.1:
            return 'ko', 0.7
        elif cjk_count / total > 0.3:
            # 簡繁體判斷（簡單版本）
            # 這裡可以加入更精細的簡繁體判斷邏輯
            return 'zh-TW', 0.6
        elif latin_count / total > 0.5:
            return 'en', 0.6
        
        return 'zh-TW', 0.5  # 預設繁體中文
    
    def _build_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """
        組裝翻譯 Prompt
        
        Args:
            text: 原文
            source_language: 來源語言代碼
            target_language: 目標語言代碼
            
        Returns:
            完整的 Prompt
        """
        # 取得語言名稱
        source_name = self.LANGUAGE_NAMES.get(source_language, source_language)
        target_name = self.LANGUAGE_NAMES.get(target_language, target_language)
        
        # 清理文字（FR-038 Prompt 注入防護）
        sanitized_text = self._sanitize_text(text)
        
        # 取得 Prompt 範本
        template = ConfigLoader.get_prompt_template('translation')
        
        return template.format(
            source_language=source_name,
            target_language=target_name,
            text=sanitized_text,
        )
    
    def _sanitize_text(self, text: str) -> str:
        """
        清理文字，防止 Prompt 注入（FR-038）
        
        Args:
            text: 原始文字
            
        Returns:
            清理後的文字
        """
        # 移除可能的 Prompt 控制字元
        # 保留換行符號以支援 FR-006
        sanitized = text
        
        # 移除可能的指令分隔符
        dangerous_patterns = [
            r'\[INST\]',
            r'\[/INST\]',
            r'<<SYS>>',
            r'<</SYS>>',
            r'###',
            r'---',
            r'```',
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized)
        
        return sanitized
    
    def _clean_output(self, text: str) -> str:
        """
        清理模型輸出
        
        Args:
            text: 模型輸出
            
        Returns:
            清理後的文字
        """
        # 移除開頭和結尾的空白
        cleaned = text.strip()
        
        # 移除可能的引號包裹
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        return cleaned
    
    def _create_error_response(
        self,
        request: TranslationRequest,
        error_code: str,
        start_time: float,
        message: str = None,
    ) -> TranslationResponse:
        """
        建立錯誤回應
        
        Args:
            request: 翻譯請求
            error_code: 錯誤代碼
            start_time: 開始時間
            message: 錯誤訊息（可選）
            
        Returns:
            TranslationResponse 錯誤回應
        """
        from translator.errors import get_error_message
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return TranslationResponse(
            request_id=request.request_id,
            status=TranslationStatus.FAILED,
            processing_time_ms=processing_time_ms,
            execution_mode=self._model_service.get_execution_mode() or ExecutionMode.CPU,
            error_code=error_code,
            error_message=message or get_error_message(error_code),
        )


# 全域服務實例
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """取得 TranslationService 實例"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service
