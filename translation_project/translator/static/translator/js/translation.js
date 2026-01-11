/**
 * 翻譯系統前端核心 JavaScript
 * Translation System Core JavaScript
 * 
 * 提供：
 * - 字數計算 (FR-005)
 * - 剪貼簿操作
 * - HTMX 事件處理
 * - 鍵盤快捷鍵
 */

(function() {
    'use strict';

    // ===== 常數定義 =====
    const MAX_CHAR_LENGTH = 10000;
    const WARN_CHAR_LENGTH = 8000;
    const DEBOUNCE_DELAY = 100;

    // ===== 工具函數 =====
    
    /**
     * 防抖函數
     * @param {Function} func - 要防抖的函數
     * @param {number} wait - 等待時間（毫秒）
     * @returns {Function} 防抖後的函數
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 格式化數字（加入千分位）
     * @param {number} num - 數字
     * @returns {string} 格式化後的字串
     */
    function formatNumber(num) {
        return num.toLocaleString('zh-TW');
    }

    // ===== 字數計算功能 (FR-005) =====
    
    /**
     * 計算文字長度
     * @param {string} text - 文字內容
     * @returns {number} 字元數
     */
    function countCharacters(text) {
        return text ? text.length : 0;
    }

    /**
     * 更新字數顯示
     * @param {HTMLTextAreaElement} textarea - 輸入框元素
     * @param {HTMLElement} counter - 計數器元素
     */
    function updateCharCounter(textarea, counter) {
        const count = countCharacters(textarea.value);
        const formattedCount = formatNumber(count);
        const formattedMax = formatNumber(MAX_CHAR_LENGTH);
        
        counter.textContent = `${formattedCount} / ${formattedMax} 字元`;
        
        // 更新樣式
        counter.classList.remove('warning', 'error');
        if (count > MAX_CHAR_LENGTH) {
            counter.classList.add('error');
        } else if (count > WARN_CHAR_LENGTH) {
            counter.classList.add('warning');
        }
    }

    /**
     * 初始化字數計算
     */
    function initCharCounter() {
        const textarea = document.getElementById('source-text');
        const counter = document.querySelector('.char-count');
        
        if (textarea && counter) {
            // 初始更新
            updateCharCounter(textarea, counter);
            
            // 監聽輸入事件（防抖）
            textarea.addEventListener('input', debounce(function() {
                updateCharCounter(textarea, counter);
            }, DEBOUNCE_DELAY));
        }
    }

    // ===== 剪貼簿功能 =====
    
    /**
     * 複製文字到剪貼簿
     * @param {string} text - 要複製的文字
     * @returns {Promise<boolean>} 是否成功
     */
    async function copyToClipboard(text) {
        try {
            // 優先使用現代 Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
                showToast('已複製到剪貼簿！', 'success');
                return true;
            }
            
            // 降級使用 execCommand（舊瀏覽器）
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
                showToast('已複製到剪貼簿！', 'success');
                return true;
            }
            
            throw new Error('execCommand 複製失敗');
            
        } catch (err) {
            console.error('複製失敗:', err);
            showToast('複製失敗，請手動選取複製', 'error');
            return false;
        }
    }

    // ===== Toast 提示訊息 =====
    
    /**
     * 顯示提示訊息
     * @param {string} message - 訊息內容
     * @param {string} type - 類型 ('success' | 'error' | 'warning' | 'info')
     * @param {number} duration - 顯示時間（毫秒）
     */
    function showToast(message, type = 'info', duration = 2000) {
        // 移除現有 toast
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        
        // 樣式
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 8px;
            color: ${type === 'warning' ? '#333' : 'white'};
            background-color: ${colors[type] || colors.info};
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 9999;
            animation: toastSlideIn 0.3s ease;
            font-size: 0.9rem;
        `;
        
        document.body.appendChild(toast);
        
        // 自動移除
        setTimeout(function() {
            toast.style.animation = 'toastSlideOut 0.3s ease';
            setTimeout(function() {
                toast.remove();
            }, 300);
        }, duration);
    }

    // ===== 鍵盤快捷鍵 =====
    
    /**
     * 初始化鍵盤快捷鍵
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Enter: 執行翻譯
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                const translateBtn = document.querySelector('[x-data] button.btn-primary');
                if (translateBtn && !translateBtn.disabled) {
                    translateBtn.click();
                }
            }
            
            // Ctrl/Cmd + Shift + C: 複製翻譯結果
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                const resultText = document.querySelector('.translated-text, .result-text span');
                if (resultText && resultText.textContent.trim()) {
                    copyToClipboard(resultText.textContent);
                }
            }
            
            // Escape: 清除錯誤訊息
            if (e.key === 'Escape') {
                const errorMsg = document.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.style.display = 'none';
                }
            }
        });
    }

    // ===== HTMX 事件處理 =====
    
    /**
     * 初始化 HTMX 事件監聽
     */
    function initHtmxHandlers() {
        // HTMX 請求開始
        document.body.addEventListener('htmx:beforeRequest', function(e) {
            // 顯示載入狀態
            const target = e.detail.target;
            if (target) {
                target.classList.add('htmx-loading');
            }
        });
        
        // HTMX 請求結束
        document.body.addEventListener('htmx:afterRequest', function(e) {
            const target = e.detail.target;
            if (target) {
                target.classList.remove('htmx-loading');
            }
        });
        
        // HTMX 請求錯誤
        document.body.addEventListener('htmx:responseError', function(e) {
            console.error('HTMX 請求錯誤:', e.detail);
            showToast('請求失敗，請稍後再試', 'error');
        });
        
        // HTMX 網路錯誤
        document.body.addEventListener('htmx:sendError', function() {
            showToast('網路連線失敗，請檢查網路狀態', 'error');
        });
    }

    // ===== 表單驗證 =====
    
    /**
     * 驗證翻譯請求
     * @param {string} text - 來源文字
     * @param {string} targetLang - 目標語言
     * @returns {{valid: boolean, message: string}}
     */
    function validateTranslation(text, targetLang) {
        if (!text || !text.trim()) {
            return { valid: false, message: '請輸入要翻譯的文字' };
        }
        
        if (text.length > MAX_CHAR_LENGTH) {
            return { 
                valid: false, 
                message: `文字長度超過 ${formatNumber(MAX_CHAR_LENGTH)} 字元限制` 
            };
        }
        
        if (!targetLang) {
            return { valid: false, message: '請選擇目標語言' };
        }
        
        return { valid: true, message: '' };
    }

    // ===== 歷史記錄管理 =====
    
    const HistoryManager = {
        STORAGE_KEY: 'translationHistory',
        MAX_ITEMS: 20,
        
        /**
         * 取得歷史記錄
         * @returns {Array} 歷史記錄陣列
         */
        getAll: function() {
            try {
                return JSON.parse(sessionStorage.getItem(this.STORAGE_KEY) || '[]');
            } catch (e) {
                console.error('讀取歷史記錄失敗:', e);
                return [];
            }
        },
        
        /**
         * 新增記錄
         * @param {Object} item - 記錄項目
         */
        add: function(item) {
            try {
                let history = this.getAll();
                history.unshift({
                    ...item,
                    timestamp: new Date().toISOString()
                });
                
                if (history.length > this.MAX_ITEMS) {
                    history = history.slice(0, this.MAX_ITEMS);
                }
                
                sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
            } catch (e) {
                console.error('儲存歷史記錄失敗:', e);
            }
        },
        
        /**
         * 清除所有記錄
         */
        clear: function() {
            sessionStorage.removeItem(this.STORAGE_KEY);
        },
        
        /**
         * 刪除單筆記錄
         * @param {string} id - 記錄 ID
         */
        remove: function(id) {
            try {
                let history = this.getAll();
                history = history.filter(item => item.id !== id);
                sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
            } catch (e) {
                console.error('刪除歷史記錄失敗:', e);
            }
        }
    };

    // ===== 設定管理 =====
    
    const SettingsManager = {
        STORAGE_KEY: 'userSettings',
        
        /**
         * 取得所有設定
         * @returns {Object} 設定物件
         */
        getAll: function() {
            try {
                return JSON.parse(sessionStorage.getItem(this.STORAGE_KEY) || '{}');
            } catch (e) {
                console.error('讀取設定失敗:', e);
                return {};
            }
        },
        
        /**
         * 取得單一設定
         * @param {string} key - 設定鍵
         * @param {*} defaultValue - 預設值
         * @returns {*} 設定值
         */
        get: function(key, defaultValue) {
            const settings = this.getAll();
            return settings[key] !== undefined ? settings[key] : defaultValue;
        },
        
        /**
         * 設定值
         * @param {string} key - 設定鍵
         * @param {*} value - 設定值
         */
        set: function(key, value) {
            try {
                const settings = this.getAll();
                settings[key] = value;
                sessionStorage.setItem(this.STORAGE_KEY, JSON.stringify(settings));
            } catch (e) {
                console.error('儲存設定失敗:', e);
            }
        },
        
        /**
         * 清除所有設定
         */
        clear: function() {
            sessionStorage.removeItem(this.STORAGE_KEY);
        }
    };

    // ===== CSS 動畫注入 =====
    
    function injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes toastSlideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes toastSlideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
            
            .htmx-loading {
                position: relative;
            }
            
            .htmx-loading::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
            }
        `;
        document.head.appendChild(style);
    }

    // ===== 初始化 =====
    
    function init() {
        // 注入樣式
        injectStyles();
        
        // 初始化各功能
        initCharCounter();
        initKeyboardShortcuts();
        initHtmxHandlers();
        
        console.log('翻譯系統前端已初始化');
    }

    // DOM 載入完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ===== 匯出全域函數 =====
    window.TranslationApp = {
        copyToClipboard: copyToClipboard,
        showToast: showToast,
        validateTranslation: validateTranslation,
        HistoryManager: HistoryManager,
        SettingsManager: SettingsManager,
        formatNumber: formatNumber
    };

})();
