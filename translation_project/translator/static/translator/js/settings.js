/**
 * 翻譯系統設定管理模組
 * Translation System Settings Management Module
 * 
 * 提供：
 * - 設定儲存與讀取（sessionStorage）
 * - 主題切換
 * - 字體大小調整
 * - 設定同步與套用
 */

(function() {
    'use strict';

    // ===== 常數定義 =====
    const STORAGE_KEY = 'userSettings';
    const THEME_KEY = 'theme';
    const FONT_SIZE_KEY = 'fontSize';

    // 預設設定
    const DEFAULT_SETTINGS = {
        // 語言設定
        defaultSourceLang: 'auto',
        defaultTargetLang: 'en',
        
        // 翻譯品質
        quality: 'standard',
        
        // 介面設定
        theme: 'light',          // 'light' | 'dark' | 'auto'
        fontSize: 'medium',      // 'small' | 'medium' | 'large'
        
        // 功能設定
        autoDetect: true,        // 自動語言偵測
        saveHistory: true,       // 儲存翻譯歷史
        showConfidence: true,    // 顯示信心度
        
        // 進階設定
        keyboardShortcuts: true, // 鍵盤快捷鍵
        soundEffects: false,     // 音效
        autoTranslate: false,    // 自動翻譯（輸入停止後）
        autoTranslateDelay: 1500, // 自動翻譯延遲（毫秒）
    };

    // ===== SettingsManager 類別 =====
    class SettingsManager {
        constructor() {
            this._settings = null;
            this._listeners = new Map();
        }

        /**
         * 初始化設定管理器
         */
        init() {
            this._settings = this._loadSettings();
            this._applySettings();
            this._setupSystemThemeListener();
            console.log('設定管理器已初始化');
        }

        /**
         * 取得所有設定
         * @returns {Object} 完整的設定物件
         */
        getAll() {
            if (!this._settings) {
                this._settings = this._loadSettings();
            }
            return { ...this._settings };
        }

        /**
         * 取得單一設定值
         * @param {string} key - 設定鍵
         * @param {*} defaultValue - 預設值
         * @returns {*} 設定值
         */
        get(key, defaultValue = undefined) {
            const settings = this.getAll();
            return settings[key] !== undefined ? settings[key] : defaultValue;
        }

        /**
         * 設定單一值
         * @param {string} key - 設定鍵
         * @param {*} value - 設定值
         */
        set(key, value) {
            this._settings[key] = value;
            this._saveSettings();
            this._applySetting(key, value);
            this._notifyListeners(key, value);
        }

        /**
         * 批量更新設定
         * @param {Object} updates - 要更新的設定
         */
        update(updates) {
            Object.assign(this._settings, updates);
            this._saveSettings();
            
            for (const [key, value] of Object.entries(updates)) {
                this._applySetting(key, value);
                this._notifyListeners(key, value);
            }
        }

        /**
         * 重設為預設值
         */
        reset() {
            this._settings = { ...DEFAULT_SETTINGS };
            this._saveSettings();
            this._applySettings();
            this._notifyListeners('*', this._settings);
        }

        /**
         * 訂閱設定變更
         * @param {string} key - 設定鍵（'*' 表示所有）
         * @param {Function} callback - 回調函數
         * @returns {Function} 取消訂閱的函數
         */
        subscribe(key, callback) {
            if (!this._listeners.has(key)) {
                this._listeners.set(key, new Set());
            }
            this._listeners.get(key).add(callback);

            return () => {
                this._listeners.get(key).delete(callback);
            };
        }

        // ===== 私有方法 =====

        /**
         * 從 sessionStorage 載入設定
         * @returns {Object} 設定物件
         */
        _loadSettings() {
            try {
                const stored = sessionStorage.getItem(STORAGE_KEY);
                if (stored) {
                    const parsed = JSON.parse(stored);
                    return { ...DEFAULT_SETTINGS, ...parsed };
                }
            } catch (e) {
                console.error('載入設定失敗:', e);
            }
            return { ...DEFAULT_SETTINGS };
        }

        /**
         * 儲存設定到 sessionStorage
         */
        _saveSettings() {
            try {
                sessionStorage.setItem(STORAGE_KEY, JSON.stringify(this._settings));
                
                // 同步特定設定到獨立的儲存鍵（向後相容）
                sessionStorage.setItem('quality', this._settings.quality);
                localStorage.setItem(THEME_KEY, this._settings.theme);
                localStorage.setItem(FONT_SIZE_KEY, this._settings.fontSize);
            } catch (e) {
                console.error('儲存設定失敗:', e);
            }
        }

        /**
         * 套用所有設定
         */
        _applySettings() {
            for (const [key, value] of Object.entries(this._settings)) {
                this._applySetting(key, value);
            }
        }

        /**
         * 套用單一設定
         * @param {string} key - 設定鍵
         * @param {*} value - 設定值
         */
        _applySetting(key, value) {
            switch (key) {
                case 'theme':
                    this._applyTheme(value);
                    break;
                case 'fontSize':
                    this._applyFontSize(value);
                    break;
            }
        }

        /**
         * 套用主題
         * @param {string} theme - 主題名稱
         */
        _applyTheme(theme) {
            const html = document.documentElement;
            html.classList.remove('light', 'dark');

            if (theme === 'auto') {
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                html.classList.add(prefersDark ? 'dark' : 'light');
            } else {
                html.classList.add(theme);
            }
        }

        /**
         * 套用字體大小
         * @param {string} size - 字體大小
         */
        _applyFontSize(size) {
            const html = document.documentElement;
            html.classList.remove('font-small', 'font-medium', 'font-large');
            html.classList.add(`font-${size}`);
        }

        /**
         * 設定系統主題變更監聽
         */
        _setupSystemThemeListener() {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                if (this._settings.theme === 'auto') {
                    this._applyTheme('auto');
                }
            });
        }

        /**
         * 通知監聽器
         * @param {string} key - 設定鍵
         * @param {*} value - 設定值
         */
        _notifyListeners(key, value) {
            // 通知特定鍵的監聽器
            if (this._listeners.has(key)) {
                for (const callback of this._listeners.get(key)) {
                    try {
                        callback(value, key);
                    } catch (e) {
                        console.error('設定監聽器錯誤:', e);
                    }
                }
            }

            // 通知通用監聽器
            if (this._listeners.has('*') && key !== '*') {
                for (const callback of this._listeners.get('*')) {
                    try {
                        callback(value, key);
                    } catch (e) {
                        console.error('設定監聽器錯誤:', e);
                    }
                }
            }
        }
    }

    // ===== 主題管理 =====
    const ThemeManager = {
        THEMES: ['light', 'dark', 'auto'],

        /**
         * 取得當前主題
         * @returns {string} 主題名稱
         */
        getCurrent() {
            return settings.get('theme', 'light');
        },

        /**
         * 設定主題
         * @param {string} theme - 主題名稱
         */
        set(theme) {
            if (this.THEMES.includes(theme)) {
                settings.set('theme', theme);
            }
        },

        /**
         * 切換主題
         */
        toggle() {
            const current = this.getCurrent();
            const next = current === 'light' ? 'dark' : 'light';
            this.set(next);
        },

        /**
         * 取得有效的主題（解析 auto）
         * @returns {string} 'light' 或 'dark'
         */
        getEffective() {
            const theme = this.getCurrent();
            if (theme === 'auto') {
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            return theme;
        },
    };

    // ===== 字體大小管理 =====
    const FontSizeManager = {
        SIZES: ['small', 'medium', 'large'],
        SIZE_VALUES: {
            small: '14px',
            medium: '16px',
            large: '18px',
        },

        /**
         * 取得當前字體大小
         * @returns {string} 字體大小名稱
         */
        getCurrent() {
            return settings.get('fontSize', 'medium');
        },

        /**
         * 設定字體大小
         * @param {string} size - 字體大小名稱
         */
        set(size) {
            if (this.SIZES.includes(size)) {
                settings.set('fontSize', size);
            }
        },

        /**
         * 增大字體
         */
        increase() {
            const current = this.getCurrent();
            const index = this.SIZES.indexOf(current);
            if (index < this.SIZES.length - 1) {
                this.set(this.SIZES[index + 1]);
            }
        },

        /**
         * 縮小字體
         */
        decrease() {
            const current = this.getCurrent();
            const index = this.SIZES.indexOf(current);
            if (index > 0) {
                this.set(this.SIZES[index - 1]);
            }
        },
    };

    // ===== 品質設定管理 =====
    const QualityManager = {
        MODES: ['fast', 'standard', 'quality'],
        MODE_NAMES: {
            fast: '快速模式',
            standard: '標準模式',
            quality: '高品質模式',
        },

        /**
         * 取得當前品質模式
         * @returns {string} 品質模式
         */
        getCurrent() {
            return settings.get('quality', 'standard');
        },

        /**
         * 設定品質模式
         * @param {string} mode - 品質模式
         */
        set(mode) {
            if (this.MODES.includes(mode)) {
                settings.set('quality', mode);
            }
        },

        /**
         * 取得品質模式的顯示名稱
         * @param {string} mode - 品質模式
         * @returns {string} 顯示名稱
         */
        getName(mode) {
            return this.MODE_NAMES[mode] || mode;
        },
    };

    // ===== 建立全域實例 =====
    const settings = new SettingsManager();

    // DOM 載入完成後初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => settings.init());
    } else {
        settings.init();
    }

    // ===== 匯出全域介面 =====
    window.AppSettings = settings;
    window.ThemeManager = ThemeManager;
    window.FontSizeManager = FontSizeManager;
    window.QualityManager = QualityManager;

    console.log('設定模組已載入');

})();
