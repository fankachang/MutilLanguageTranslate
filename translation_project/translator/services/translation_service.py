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

    # 用於 Prompt 的語言名稱（盡量使用英文/代碼，降低模型誤解機率）
    LANGUAGE_PROMPT_NAMES = {
        'zh-TW': 'Traditional Chinese (zh-TW)',
        'zh-CN': 'Simplified Chinese (zh-CN)',
        'en': 'English (en)',
        'ja': 'Japanese (ja)',
        'ko': 'Korean (ko)',
        'fr': 'French (fr)',
        'de': 'German (de)',
        'es': 'Spanish (es)',
        'auto': 'auto',
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
        
        # 呼叫模型（一次性翻譯整個文字）
        translation_logger.debug(
            "開始翻譯 | ID=%s | 文字長度=%d",
            request.request_id,
            len(request.text),
        )
        raw_text = self._model_service.generate(
            prompt=prompt,
            quality=request.quality,
        )
        translation_logger.debug(
            "模型生成完成 | ID=%s | 輸出長度=%d",
            request.request_id,
            len(raw_text),
        )

        # 便於排查「回空字串」：先記錄清理前片段
        print(f"\n=== DEBUG | ID={request.request_id} ===")
        print(f"模型原始輸出: {raw_text!r}")
        translation_logger.info(
            "模型原始輸出片段 | ID=%s | preview=%r",
            request.request_id,
            raw_text[:300],
        )
        
        # 清理輸出
        cleaned_text = self._clean_output(raw_text)
        translated_text = self._extract_best_translation_line(
            cleaned_text or raw_text,
            request.target_language,
        )
        print(f"清理後輸出: {translated_text!r}")
        print(f"=== END DEBUG ===\n")
        translation_logger.info(
            "清理後輸出 | ID=%s | len=%d | preview=%r",
            request.request_id,
            len(translated_text),
            translated_text[:300],
        )

        # 若模型沒有翻譯到目標語言，嘗試以更強約束的提示重試一次（避免跑題續寫）
        if (not translated_text) or (not self._looks_like_target_language(translated_text, request.target_language)):
            translation_logger.warning(
                "翻譯疑似未符合目標語言，嘗試重試 | ID=%s | target=%s",
                request.request_id,
                request.target_language,
            )
            retry_prompt = self._build_translation_prompt(
                text=request.text,
                source_language=source_lang,
                target_language=request.target_language,
                force_output_only=True,
            )
            # 重試時採用更保守參數：
            # - min_new_tokens 提高到 5，強制模型至少生成幾個 token（避免直接 EOS）
            # - max_new_tokens 限制，避免續寫
            # - 確保 do_sample/temperature/top_p 生效
            retry_raw = self._model_service.generate(
                prompt=retry_prompt,
                quality=request.quality,
                generation_overrides={
                    'min_new_tokens': 5,  # 提高到 5，避免直接輸出 EOS
                    'max_new_tokens': 64,
                    'num_beams': 1,
                    'do_sample': True,
                    'temperature': 0.5,  # 稍微提高以增加多樣性
                    'top_p': 0.9,
                    'repetition_penalty': 1.1,
                },
            )
            print(f"\n=== RETRY DEBUG | ID={request.request_id} ===")
            print(f"重試原始輸出: {retry_raw!r}")
            retry_cleaned = self._clean_output(retry_raw)
            retry_text = self._extract_best_translation_line(
                retry_cleaned or retry_raw,
                request.target_language,
            )
            print(f"重試清理後: {retry_text!r}")
            print(f"=== END RETRY ===\n")
            if retry_text and self._looks_like_target_language(retry_text, request.target_language):
                translated_text = retry_text

        # UI 需求：若原文為單行（不含換行），只輸出第一行譯文
        if '\n' not in request.text:
            non_empty_lines = [ln.strip() for ln in translated_text.splitlines() if ln.strip()]
            if non_empty_lines:
                translated_text = non_empty_lines[0]
            else:
                translated_text = translated_text.strip()
        
        return {
            'translated_text': translated_text,
            'detected_language': detected_language,
            'confidence_score': confidence_score,
        }

    def _extract_best_translation_line(self, text: str, target_language: str) -> str:
        """從模型輸出中挑出最像譯文的一行，避免回傳分隔線/純符號。"""
        if not text:
            return ''

        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if ln]

        def is_symbol_only(s: str) -> bool:
            # 只包含標點、符號、空白的行
            return re.fullmatch(r"[\s\-‐‑–—_=~`'\".,:;!?()\[\]{}<>|/\\*+^%$#@!]+", s) is not None

        # 先丟掉純符號行
        candidates = [ln for ln in lines if not is_symbol_only(ln)]
        if not candidates:
            return ''

        # 依目標語言選擇第一個合格候選
        if target_language == 'en':
            for ln in candidates:
                if len(re.findall(r'[A-Za-z]', ln)) >= 3:
                    return ln
        if target_language in ('zh-TW', 'zh-CN'):
            for ln in candidates:
                if len(re.findall(r'[\u4e00-\u9fff]', ln)) >= 3:
                    return ln

        # 其他語言：回第一個非符號行
        return candidates[0]

    def _looks_like_target_language(self, text: str, target_language: str) -> bool:
        """粗略判斷輸出是否符合目標語言（避免模型未翻譯、直接續寫原語言）。"""
        if not text or not text.strip():
            return False

        sample = text.strip()[:200]

        # 針對英文：至少要有一定比例的拉丁字母
        if target_language == 'en':
            latin = len(re.findall(r'[A-Za-z]', sample))
            cjk = len(re.findall(r'[\u4e00-\u9fff]', sample))
            # 有英文字母且英文比重不低於中文
            return latin >= 3 and latin >= cjk

        # 針對中文（繁/簡）：至少要有一定比例的 CJK 字元
        if target_language in ('zh-TW', 'zh-CN'):
            cjk = len(re.findall(r'[\u4e00-\u9fff]', sample))
            latin = len(re.findall(r'[A-Za-z]', sample))
            return cjk >= 3 and cjk >= latin

        # 其他語言先不做嚴格檢查，避免誤判
        return True
    
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
            logger.warning("語言偵測失敗: %s", e)
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
        force_output_only: bool = False,
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
        # 取得語言名稱（Prompt 使用英文/代碼版本）
        source_name = self.LANGUAGE_PROMPT_NAMES.get(source_language, source_language)
        target_name = self.LANGUAGE_PROMPT_NAMES.get(target_language, target_language)
        
        # 清理文字（FR-038 Prompt 注入防護）
        sanitized_text = self._sanitize_text(text)
        
        # 使用強約束的 [INST] 指令格式。
        # 注意：所有約束必須放在同一個指令區塊內，不能放在 [/INST] 後面，
        # 否則模型容易把它當作要續寫的上下文而非指令。
        extra_constraints = ""
        if force_output_only:
            extra_constraints = (
                "\n- 只輸出一行譯文。\n"
                "- 不要輸出原文。\n"
                "- 不要列點、不要章節標題、不要補充說明、不要延伸內容。\n"
            )

        return (
            "[INST] 你是專業翻譯員。你的任務是『翻譯』，不是改寫或續寫。\n"
            f"請將下列文字從 {source_name} 翻譯成 {target_name}。\n"
            "要求：\n"
            "- 只輸出譯文，不要輸出任何其他文字。\n"
            "- 不要解釋、不要求澄清、不提出問題。\n"
            "- 不要產生章節、目錄或延伸內容。\n"
            f"{extra_constraints}"
            "\n原文：\n"
            f"{sanitized_text}\n"
            "[/INST]"
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
        
        移除模型可能產生的 prompt 標記（如「原文：」、「翻譯：」等），
        只保留純粹的翻譯結果。關鍵在於只取第一段有效翻譯，避免模型
        重複輸出造成的問題。
        
        Args:
            text: 模型輸出的完整文字（已經是翻譯完成的結果）
            
        Returns:
            清理後的翻譯文字
        """
        cleaned = text.strip()

        # 移除 Llama/TAIDE prompt 標記（模型有時會把這些也輸出）
        cleaned = re.sub(r'\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()

        # 移除模型常見的前綴裝飾（分隔線/箭頭/引用符）
        # 例如："----------------------> This is a book."、">>> Translation" 等
        cleaned = re.sub(r'^\s*[\-‐‑–—_=]{3,}\s*(?:>+)?\s*', '', cleaned)
        cleaned = re.sub(r'^\s*(?:>+|\|+)\s*', '', cleaned)
        
        # 移除可能的引號包裹
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1].strip()
        
        # 定義需要截斷的標記（這些標記之後的內容都是重複或無關的）
        stop_markers = [
            '中文翻譯：', '英文翻譯：', '日文翻譯：', '韓文翻譯：',
            '繁體中文翻譯：', '簡體中文翻譯：',
            '法文翻譯：', '德文翻譯：', '西班牙文翻譯：',
            'Chinese translation:', 'English translation:',
            'Japanese translation:', 'Korean translation:',
            'Translation:', 'Original:',
            '原文：', '翻譯：',
            '原文:', '翻譯:',
        ]
        
        # 在第一個停止標記處截斷。
        # 注意：若標記出現在開頭（idx==0），代表模型以「標記:內容」格式輸出，
        # 此時不應截斷成空字串，而是先移除該標記，讓後續解析邏輯保留內容。
        for marker in stop_markers:
            idx = cleaned.find(marker)
            if idx == -1:
                continue
            # 標記前只有空白（例如輸出以 "\nTranslation:" 開頭）時，也視為開頭標記
            if idx == 0 or (idx <= 2 and cleaned[:idx].strip() == ''):
                cleaned = cleaned[idx + len(marker):].lstrip()
                continue
            cleaned = cleaned[:idx].strip()
        
        # 處理可能包含標記的多行輸出
        lines = cleaned.split('\n')
        result_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # 僅當已有結果時才保留空行（避免開頭空行）
                if result_lines:
                    result_lines.append('')
                continue

            # 跳過純符號/分隔線行（避免像 "... ------ !!!" 這類雜訊）
            if re.fullmatch(r"[\-‐‑–—_=~`'\".,:;!?()\[\]{}<>|/\\*+^%$#@!\s]+", line):
                continue
            
            # 跳過純標記行（整行只有標記）
            skip_patterns = [
                '原文：', '翻譯：', 'Translation:', 'Original:',
                '原文', '翻譯', '中文翻譯：', '英文翻譯：',
            ]
            if line in skip_patterns:
                continue
            
            # 跳過「原文：內容」格式的行
            if line.startswith(('原文：', 'Original:', '原文:')):
                continue
            
            # 處理「翻譯：內容」格式 - 只保留內容（只處理第一次出現）
            if line.startswith(('翻譯：', 'Translation:', '翻譯:')):
                if not result_lines:  # 只在沒有結果時處理
                    content = line.split('：', 1)[-1].strip() if '：' in line else line.split(':', 1)[-1].strip()
                    if content:
                        result_lines.append(content)
                continue
            
            # 保留其他內容（這才是翻譯結果）
            result_lines.append(line)
        
        # 組合結果並移除多餘空行
        cleaned = '\n'.join(result_lines)
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # 最多保留一個空行
        
        # 移除結尾可能的重複標點
        cleaned = re.sub(r'([。！？.!?])\1+$', r'\1', cleaned)
        
        return cleaned.strip()
    
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
