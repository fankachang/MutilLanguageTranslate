/**
 * 翻譯系統前端驗證模組
 * Translation System Frontend Validation Module
 * 
 * 提供：
 * - 空白檢查
 * - 字數限制檢查
 * - 相同語言檢查
 * - 即時驗證回饋
 * 
 * FR-005: 即時字數統計
 * FR-038: Prompt 注入防護（前端層級）
 */

(function() {
    'use strict';

    // ===== 常數定義 =====
    const VALIDATION_CONFIG = {
        MAX_CHAR_LENGTH: 10000,      // 最大字元數
        WARN_CHAR_LENGTH: 8000,      // 警告字元數
        MIN_CHAR_LENGTH: 1,          // 最小字元數
    };

    // ===== 驗證結果類別 =====
    class ValidationResult {
        constructor(isValid, errorCode = null, errorMessage = null, warningMessage = null) {
            this.isValid = isValid;
            this.errorCode = errorCode;
            this.errorMessage = errorMessage;
            this.warningMessage = warningMessage;
        }

        static success() {
            return new ValidationResult(true);
        }

        static error(code, message) {
            return new ValidationResult(false, code, message);
        }

        static warning(message) {
            const result = new ValidationResult(true);
            result.warningMessage = message;
            return result;
        }
    }

    // ===== 錯誤代碼與訊息對照 =====
    const ERROR_MESSAGES = {
        'VALIDATION_EMPTY_TEXT': '請輸入要翻譯的文字',
        'VALIDATION_TEXT_TOO_LONG': '文字長度超過 10,000 字元，請縮短後再試',
        'VALIDATION_SAME_LANGUAGE': '來源語言與目標語言不可相同',
        'VALIDATION_INVALID_LANGUAGE': '無效的語言代碼',
        'VALIDATION_WHITESPACE_ONLY': '請輸入有效的文字內容，不能只有空白',
        'NETWORK_ERROR': '網路連線失敗，請檢查網路狀態',
        'SERVICE_UNAVAILABLE': '翻譯服務暫時無法使用，請稍後再試',
        'QUEUE_FULL': '系統繁忙，請稍後再試',
        'TRANSLATION_TIMEOUT': '翻譯逾時，請嘗試縮短文字長度或稍後再試',
        'INTERNAL_ERROR': '系統內部錯誤，請聯繫管理員',
    };

    // ===== 驗證函數 =====

    /**
     * 驗證文字內容
     * @param {string} text - 要驗證的文字
     * @returns {ValidationResult} 驗證結果
     */
    function validateText(text) {
        // 空值檢查
        if (text === null || text === undefined) {
            return ValidationResult.error(
                'VALIDATION_EMPTY_TEXT',
                ERROR_MESSAGES['VALIDATION_EMPTY_TEXT']
            );
        }

        // 轉換為字串
        const textStr = String(text);

        // 空字串檢查
        if (textStr.length === 0) {
            return ValidationResult.error(
                'VALIDATION_EMPTY_TEXT',
                ERROR_MESSAGES['VALIDATION_EMPTY_TEXT']
            );
        }

        // 只有空白檢查
        if (textStr.trim().length === 0) {
            return ValidationResult.error(
                'VALIDATION_WHITESPACE_ONLY',
                ERROR_MESSAGES['VALIDATION_WHITESPACE_ONLY']
            );
        }

        // 字數上限檢查
        if (textStr.length > VALIDATION_CONFIG.MAX_CHAR_LENGTH) {
            return ValidationResult.error(
                'VALIDATION_TEXT_TOO_LONG',
                ERROR_MESSAGES['VALIDATION_TEXT_TOO_LONG']
            );
        }

        // 接近上限警告
        if (textStr.length > VALIDATION_CONFIG.WARN_CHAR_LENGTH) {
            return ValidationResult.warning(
                `文字長度接近上限（${textStr.length.toLocaleString('zh-TW')} / ${VALIDATION_CONFIG.MAX_CHAR_LENGTH.toLocaleString('zh-TW')} 字元）`
            );
        }

        return ValidationResult.success();
    }

    /**
     * 驗證語言選擇
     * @param {string} sourceLang - 來源語言代碼
     * @param {string} targetLang - 目標語言代碼
     * @returns {ValidationResult} 驗證結果
     */
    function validateLanguages(sourceLang, targetLang) {
        // 有效的語言代碼清單
        const validLanguages = ['zh-TW', 'zh-CN', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'auto'];

        // 來源語言驗證（可以是 auto）
        if (!validLanguages.includes(sourceLang)) {
            return ValidationResult.error(
                'VALIDATION_INVALID_LANGUAGE',
                ERROR_MESSAGES['VALIDATION_INVALID_LANGUAGE']
            );
        }

        // 目標語言驗證（不可以是 auto）
        const validTargetLanguages = validLanguages.filter(lang => lang !== 'auto');
        if (!validTargetLanguages.includes(targetLang)) {
            return ValidationResult.error(
                'VALIDATION_INVALID_LANGUAGE',
                ERROR_MESSAGES['VALIDATION_INVALID_LANGUAGE']
            );
        }

        // 相同語言檢查（來源不是 auto 時）
        if (sourceLang !== 'auto' && sourceLang === targetLang) {
            return ValidationResult.error(
                'VALIDATION_SAME_LANGUAGE',
                ERROR_MESSAGES['VALIDATION_SAME_LANGUAGE']
            );
        }

        return ValidationResult.success();
    }

    /**
     * 完整的翻譯請求驗證
     * @param {Object} request - 翻譯請求
     * @param {string} request.text - 原文
     * @param {string} request.sourceLang - 來源語言
     * @param {string} request.targetLang - 目標語言
     * @returns {ValidationResult} 驗證結果
     */
    function validateTranslationRequest(request) {
        const { text, sourceLang, targetLang } = request;

        // 驗證文字
        const textResult = validateText(text);
        if (!textResult.isValid) {
            return textResult;
        }

        // 驗證語言
        const langResult = validateLanguages(sourceLang, targetLang);
        if (!langResult.isValid) {
            return langResult;
        }

        // 如果文字驗證有警告，返回該警告
        if (textResult.warningMessage) {
            return textResult;
        }

        return ValidationResult.success();
    }

    /**
     * 取得錯誤代碼對應的中文訊息
     * @param {string} errorCode - 錯誤代碼
     * @returns {string} 中文錯誤訊息
     */
    function getErrorMessage(errorCode) {
        return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES['INTERNAL_ERROR'];
    }

    // ===== UI 整合函數 =====

    /**
     * 顯示驗證錯誤
     * @param {HTMLElement} element - 顯示錯誤的元素
     * @param {ValidationResult} result - 驗證結果
     */
    function showValidationError(element, result) {
        if (!element) return;

        if (!result.isValid) {
            element.textContent = result.errorMessage;
            element.className = 'validation-message validation-error fade-in';
            element.style.display = 'block';
        } else if (result.warningMessage) {
            element.textContent = result.warningMessage;
            element.className = 'validation-message validation-warning fade-in';
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }

    /**
     * 清除驗證訊息
     * @param {HTMLElement} element - 顯示訊息的元素
     */
    function clearValidationMessage(element) {
        if (element) {
            element.style.display = 'none';
            element.textContent = '';
            element.className = 'validation-message';
        }
    }

    /**
     * 設定輸入框的驗證狀態樣式
     * @param {HTMLElement} input - 輸入框元素
     * @param {ValidationResult} result - 驗證結果
     */
    function setInputValidationState(input, result) {
        if (!input) return;

        input.classList.remove('input-error', 'input-warning', 'input-valid');

        if (!result.isValid) {
            input.classList.add('input-error');
        } else if (result.warningMessage) {
            input.classList.add('input-warning');
        } else {
            input.classList.add('input-valid');
        }
    }

    /**
     * 即時驗證輸入框
     * @param {HTMLTextAreaElement} textarea - 文字輸入框
     * @param {HTMLElement} messageElement - 訊息顯示元素
     * @param {Object} options - 選項
     */
    function attachRealTimeValidation(textarea, messageElement, options = {}) {
        if (!textarea) return;

        const debounceDelay = options.debounceDelay || 300;
        let debounceTimer;

        const validate = () => {
            const result = validateText(textarea.value);
            showValidationError(messageElement, result);
            setInputValidationState(textarea, result);

            // 觸發自訂事件
            textarea.dispatchEvent(new CustomEvent('validation', {
                detail: result
            }));
        };

        textarea.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(validate, debounceDelay);
        });

        textarea.addEventListener('blur', validate);
    }

    // ===== 危險內容檢測（FR-038 前端層級） =====

    /**
     * 檢測可能的 Prompt 注入
     * @param {string} text - 要檢測的文字
     * @returns {boolean} 是否包含可疑內容
     */
    function detectPotentialInjection(text) {
        if (!text) return false;

        // 可疑的 Prompt 控制模式
        const suspiciousPatterns = [
            /\[INST\]/i,
            /\[\/INST\]/i,
            /<<SYS>>/i,
            /<\/SYS>/i,
            /ignore previous instructions/i,
            /忽略.*指令/i,
            /system prompt/i,
        ];

        return suspiciousPatterns.some(pattern => pattern.test(text));
    }

    /**
     * 清理文字內容（移除可疑控制字元）
     * @param {string} text - 原始文字
     * @returns {string} 清理後的文字
     */
    function sanitizeText(text) {
        if (!text) return '';

        let sanitized = text;

        // 移除可疑的控制模式
        const patternsToRemove = [
            /\[INST\]/gi,
            /\[\/INST\]/gi,
            /<<SYS>>/gi,
            /<\/SYS>/gi,
        ];

        patternsToRemove.forEach(pattern => {
            sanitized = sanitized.replace(pattern, '');
        });

        return sanitized;
    }

    // ===== 匯出模組 =====
    window.TranslationValidation = {
        // 常數
        CONFIG: VALIDATION_CONFIG,
        ERROR_MESSAGES: ERROR_MESSAGES,

        // 核心驗證函數
        validateText: validateText,
        validateLanguages: validateLanguages,
        validateTranslationRequest: validateTranslationRequest,
        getErrorMessage: getErrorMessage,

        // UI 整合
        showValidationError: showValidationError,
        clearValidationMessage: clearValidationMessage,
        setInputValidationState: setInputValidationState,
        attachRealTimeValidation: attachRealTimeValidation,

        // 安全功能
        detectPotentialInjection: detectPotentialInjection,
        sanitizeText: sanitizeText,

        // 類別
        ValidationResult: ValidationResult,
    };

    console.log('翻譯系統驗證模組已載入');

})();
