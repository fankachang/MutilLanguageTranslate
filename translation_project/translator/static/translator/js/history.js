/**
 * 翻譯系統歷史記錄管理模組
 * Translation System History Management Module
 * 
 * 提供：
 * - sessionStorage 儲存歷史記錄
 * - FIFO 上限 20 筆
 * - 歷史記錄的 CRUD 操作
 * - 與翻譯頁面的整合
 */

(function() {
    'use strict';

    // ===== 常數定義 =====
    const STORAGE_KEY = 'translationHistory';
    const MAX_ITEMS = 20;
    const REUSE_KEY = 'reuseTranslation';

    // 語言代碼到名稱的映射
    const LANGUAGE_NAMES = {
        'zh-TW': '繁體中文',
        'zh-CN': '簡體中文',
        'en': '英文',
        'ja': '日文',
        'ko': '韓文',
        'fr': '法文',
        'de': '德文',
        'es': '西班牙文',
        'auto': '自動偵測',
    };

    // ===== HistoryManager 類別 =====
    class HistoryManager {
        constructor() {
            this._cache = null;
            this._listeners = new Set();
        }

        /**
         * 取得所有歷史記錄
         * @returns {Array} 歷史記錄陣列
         */
        getAll() {
            if (this._cache === null) {
                this._loadFromStorage();
            }
            return [...this._cache];
        }

        /**
         * 取得歷史記錄數量
         * @returns {number} 記錄數量
         */
        count() {
            return this.getAll().length;
        }

        /**
         * 依 ID 取得單筆記錄
         * @param {string} id - 記錄 ID
         * @returns {Object|null} 歷史記錄或 null
         */
        getById(id) {
            const items = this.getAll();
            return items.find(item => item.id === id) || null;
        }

        /**
         * 新增歷史記錄
         * @param {Object} data - 記錄資料
         * @returns {Object} 新增的記錄
         */
        add(data) {
            const items = this.getAll();
            
            const newItem = {
                id: data.request_id || this._generateId(),
                originalText: this._truncate(data.originalText || data.text, 50),
                translatedText: this._truncate(data.translatedText || data.translated_text, 50),
                fullOriginalText: data.originalText || data.text,
                fullTranslatedText: data.translatedText || data.translated_text,
                sourceLang: data.sourceLang || data.source_language,
                targetLang: data.targetLang || data.target_language,
                detectedLang: data.detectedLang || data.detected_language || null,
                confidenceScore: data.confidenceScore || data.confidence_score || null,
                timestamp: new Date().toISOString(),
                processingTimeMs: data.processingTimeMs || data.processing_time_ms || null,
            };

            // 加到開頭 (FIFO)
            items.unshift(newItem);

            // 維持上限
            if (items.length > MAX_ITEMS) {
                items.length = MAX_ITEMS;
            }

            this._saveToStorage(items);
            this._notifyListeners('add', newItem);

            return newItem;
        }

        /**
         * 刪除單筆記錄
         * @param {string} id - 記錄 ID
         * @returns {boolean} 是否刪除成功
         */
        remove(id) {
            const items = this.getAll();
            const index = items.findIndex(item => item.id === id);

            if (index === -1) {
                return false;
            }

            const removed = items.splice(index, 1)[0];
            this._saveToStorage(items);
            this._notifyListeners('remove', removed);

            return true;
        }

        /**
         * 清除所有記錄
         */
        clear() {
            this._cache = [];
            sessionStorage.removeItem(STORAGE_KEY);
            this._notifyListeners('clear', null);
        }

        /**
         * 搜尋歷史記錄
         * @param {string} query - 搜尋關鍵字
         * @returns {Array} 符合的記錄
         */
        search(query) {
            if (!query || !query.trim()) {
                return this.getAll();
            }

            const lowerQuery = query.toLowerCase();
            return this.getAll().filter(item => 
                item.fullOriginalText.toLowerCase().includes(lowerQuery) ||
                item.fullTranslatedText.toLowerCase().includes(lowerQuery)
            );
        }

        /**
         * 依語言篩選
         * @param {string} sourceLang - 來源語言
         * @param {string} targetLang - 目標語言
         * @returns {Array} 符合的記錄
         */
        filterByLanguage(sourceLang = null, targetLang = null) {
            let items = this.getAll();

            if (sourceLang) {
                items = items.filter(item => 
                    item.sourceLang === sourceLang || 
                    item.detectedLang === sourceLang
                );
            }

            if (targetLang) {
                items = items.filter(item => item.targetLang === targetLang);
            }

            return items;
        }

        /**
         * 訂閱歷史記錄變更
         * @param {Function} callback - 回調函數
         * @returns {Function} 取消訂閱的函數
         */
        subscribe(callback) {
            this._listeners.add(callback);
            return () => {
                this._listeners.delete(callback);
            };
        }

        /**
         * 設定重用翻譯資料（用於跳轉到翻譯頁面）
         * @param {Object} item - 歷史記錄項目
         */
        setReuse(item) {
            sessionStorage.setItem(REUSE_KEY, JSON.stringify(item));
        }

        /**
         * 取得並清除重用翻譯資料
         * @returns {Object|null} 重用資料或 null
         */
        getAndClearReuse() {
            const data = sessionStorage.getItem(REUSE_KEY);
            if (data) {
                sessionStorage.removeItem(REUSE_KEY);
                try {
                    return JSON.parse(data);
                } catch (e) {
                    return null;
                }
            }
            return null;
        }

        /**
         * 取得語言名稱
         * @param {string} code - 語言代碼
         * @returns {string} 語言名稱
         */
        getLanguageName(code) {
            return LANGUAGE_NAMES[code] || code;
        }

        /**
         * 格式化時間戳記
         * @param {string} timestamp - ISO 時間字串
         * @returns {string} 格式化的時間
         */
        formatTimestamp(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;

            // 1 分鐘內
            if (diff < 60000) {
                return '剛才';
            }

            // 1 小時內
            if (diff < 3600000) {
                const minutes = Math.floor(diff / 60000);
                return `${minutes} 分鐘前`;
            }

            // 今天
            if (date.toDateString() === now.toDateString()) {
                return date.toLocaleTimeString('zh-TW', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }

            // 昨天
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            if (date.toDateString() === yesterday.toDateString()) {
                return '昨天 ' + date.toLocaleTimeString('zh-TW', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }

            // 其他日期
            return date.toLocaleDateString('zh-TW', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        /**
         * 匯出歷史記錄
         * @returns {string} JSON 字串
         */
        export() {
            return JSON.stringify(this.getAll(), null, 2);
        }

        /**
         * 匯入歷史記錄
         * @param {string} jsonString - JSON 字串
         * @returns {boolean} 是否成功
         */
        import(jsonString) {
            try {
                const data = JSON.parse(jsonString);
                if (!Array.isArray(data)) {
                    return false;
                }

                // 合併並去重
                const currentItems = this.getAll();
                const existingIds = new Set(currentItems.map(item => item.id));
                
                const newItems = data.filter(item => !existingIds.has(item.id));
                const merged = [...newItems, ...currentItems].slice(0, MAX_ITEMS);

                this._saveToStorage(merged);
                this._notifyListeners('import', merged);

                return true;
            } catch (e) {
                console.error('匯入歷史記錄失敗:', e);
                return false;
            }
        }

        // ===== 私有方法 =====

        /**
         * 從 sessionStorage 載入
         */
        _loadFromStorage() {
            try {
                const data = sessionStorage.getItem(STORAGE_KEY);
                this._cache = data ? JSON.parse(data) : [];
            } catch (e) {
                console.error('載入歷史記錄失敗:', e);
                this._cache = [];
            }
        }

        /**
         * 儲存到 sessionStorage
         * @param {Array} items - 記錄陣列
         */
        _saveToStorage(items) {
            try {
                sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
                this._cache = items;
            } catch (e) {
                console.error('儲存歷史記錄失敗:', e);
            }
        }

        /**
         * 通知監聽器
         * @param {string} action - 動作類型
         * @param {*} data - 相關資料
         */
        _notifyListeners(action, data) {
            for (const callback of this._listeners) {
                try {
                    callback(action, data);
                } catch (e) {
                    console.error('歷史記錄監聽器錯誤:', e);
                }
            }
        }

        /**
         * 產生唯一 ID
         * @returns {string} UUID
         */
        _generateId() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        /**
         * 截斷文字
         * @param {string} text - 原始文字
         * @param {number} maxLength - 最大長度
         * @returns {string} 截斷後的文字
         */
        _truncate(text, maxLength) {
            if (!text) return '';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        }
    }

    // ===== 建立全域實例 =====
    const historyManager = new HistoryManager();

    // ===== 匯出全域介面 =====
    window.TranslationHistory = historyManager;

    // 向後相容：更新 TranslationApp 中的 HistoryManager
    if (window.TranslationApp && window.TranslationApp.HistoryManager) {
        // 保持向後相容性，但指向新的實例
        Object.assign(window.TranslationApp.HistoryManager, {
            getAll: () => historyManager.getAll(),
            add: (item) => historyManager.add(item),
            remove: (id) => historyManager.remove(id),
            clear: () => historyManager.clear(),
        });
    }

    console.log('歷史記錄模組已載入');

})();
