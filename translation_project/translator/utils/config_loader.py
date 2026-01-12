"""
多國語言翻譯系統 - 配置載入工具

本模組負責載入與驗證 YAML 配置檔案：
- app_config.yaml: 應用程式配置
- model_config.yaml: 模型配置
- languages.yaml: 語言配置
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from django.conf import settings

from translator.models import Language

logger = logging.getLogger('translator')


class ConfigLoader:
    """
    配置載入器
    
    負責載入與快取 YAML 配置檔案
    """
    
    # 快取
    _app_config: Optional[Dict[str, Any]] = None
    _model_config: Optional[Dict[str, Any]] = None
    _languages_config: Optional[Dict[str, Any]] = None
    _languages_list: Optional[List[Language]] = None
    
    @classmethod
    def get_app_config(cls) -> Dict[str, Any]:
        """
        取得應用程式配置
        
        Returns:
            應用程式配置字典
        """
        if cls._app_config is None:
            cls._app_config = cls._load_yaml(settings.APP_CONFIG_PATH)
        return cls._app_config
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """
        取得模型配置
        
        Returns:
            模型配置字典
        """
        if cls._model_config is None:
            cls._model_config = cls._load_yaml(settings.MODEL_CONFIG_PATH)
        return cls._model_config
    
    @classmethod
    def get_languages_config(cls) -> Dict[str, Any]:
        """
        取得語言配置
        
        Returns:
            語言配置字典
        """
        if cls._languages_config is None:
            cls._languages_config = cls._load_yaml(settings.LANGUAGES_CONFIG_PATH)
        return cls._languages_config
    
    @classmethod
    def get_languages(cls) -> List[Language]:
        """
        取得支援的語言列表
        
        Returns:
            Language 物件列表
        """
        if cls._languages_list is None:
            config = cls.get_languages_config()
            languages_data = config.get('languages', [])
            
            cls._languages_list = [
                Language(
                    code=lang['code'],
                    name=lang['name'],
                    name_en=lang['name_en'],
                    is_enabled=lang.get('is_enabled', True),
                    sort_order=lang.get('sort_order', 0),
                )
                for lang in languages_data
            ]
            
            # 依 sort_order 排序
            cls._languages_list.sort(key=lambda x: x.sort_order)
        
        return cls._languages_list
    
    @classmethod
    def get_enabled_languages(cls) -> List[Language]:
        """
        取得已啟用的語言列表
        
        Returns:
            已啟用的 Language 物件列表
        """
        return [lang for lang in cls.get_languages() if lang.is_enabled]
    
    @classmethod
    def get_language_by_code(cls, code: str) -> Optional[Language]:
        """
        依語言代碼取得語言
        
        Args:
            code: 語言代碼
            
        Returns:
            Language 物件，若不存在則返回 None
        """
        for lang in cls.get_languages():
            if lang.code == code:
                return lang
        return None
    
    @classmethod
    def is_valid_language_code(cls, code: str) -> bool:
        """
        檢查語言代碼是否有效
        
        Args:
            code: 語言代碼
            
        Returns:
            是否為有效的語言代碼
        """
        if code == "auto":
            return True
        return cls.get_language_by_code(code) is not None
    
    @classmethod
    def is_language_supported(cls, code: str) -> bool:
        """
        檢查語言是否支援（別名方法）
        
        Args:
            code: 語言代碼
            
        Returns:
            是否為支援的語言
        """
        return cls.is_valid_language_code(code)
    
    @classmethod
    def get_default_source_language(cls) -> str:
        """取得預設來源語言"""
        config = cls.get_languages_config()
        return config.get('defaults', {}).get('source_language', 'auto')
    
    @classmethod
    def get_default_target_language(cls) -> str:
        """取得預設目標語言"""
        config = cls.get_languages_config()
        return config.get('defaults', {}).get('target_language', 'zh-TW')
    
    @classmethod
    def get_translation_timeout(cls) -> int:
        """取得翻譯逾時秒數"""
        config = cls.get_app_config()
        return config.get('translation', {}).get('timeout', 120)
    
    @classmethod
    def get_max_text_length(cls) -> int:
        """取得最大文字長度"""
        config = cls.get_app_config()
        return config.get('translation', {}).get('max_text_length', 10000)
    
    @classmethod
    def get_max_concurrent(cls) -> int:
        """取得最大並發數"""
        config = cls.get_app_config()
        return config.get('concurrency', {}).get('max_concurrent', 100)
    
    @classmethod
    def get_max_queue_size(cls) -> int:
        """取得最大佇列長度"""
        config = cls.get_app_config()
        return config.get('concurrency', {}).get('max_queue_size', 100)
    
    @classmethod
    def get_admin_allowed_ips(cls) -> List[str]:
        """取得管理頁面允許的 IP 範圍"""
        config = cls.get_app_config()
        return config.get('admin_access', {}).get('allowed_ips', [
            '127.0.0.1/32',
            '192.168.0.0/16',
            '10.0.0.0/8',
            '172.16.0.0/12',
        ])
    
    @classmethod
    def get_prompt_template(cls, template_name: str) -> str:
        """
        取得 Prompt 範本
        
        Args:
            template_name: 範本名稱 (translation/language_detection)
            
        Returns:
            Prompt 範本字串
        """
        config = cls.get_model_config()
        prompts = config.get('prompts', {})
        
        defaults = {
            'translation': (
                '你是一個專業的翻譯助手。請將以下{source_language}文字翻譯成'
                '{target_language}，保持原文的格式和換行。只輸出翻譯結果，'
                '不要加入任何解釋或額外內容。\n\n原文：\n{text}\n\n翻譯：'
            ),
            'language_detection': (
                '請識別以下文字的語言，只回答語言代碼（zh-TW, zh-CN, en, ja, '
                'ko, fr, de, es 其中之一）和信心分數（0.0-1.0），格式為'
                '「語言代碼:信心分數」。\n\n文字：{text}\n\n答案：'
            ),
        }
        
        return prompts.get(template_name, defaults.get(template_name, ''))
    
    @classmethod
    def _load_yaml(cls, path: Path) -> Dict[str, Any]:
        """
        載入 YAML 檔案
        
        Args:
            path: 檔案路徑
            
        Returns:
            解析後的字典
        """
        try:
            if not path.exists():
                logger.warning(f"配置檔案不存在: {path}，使用空配置")
                return {}
            
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if data is None:
                logger.warning(f"配置檔案為空: {path}")
                return {}
                
            logger.debug(f"已載入配置檔案: {path}")
            return data
            
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析錯誤: {path} - {e}")
            return {}
        except Exception as e:
            logger.error(f"載入配置檔案失敗: {path} - {e}")
            return {}
    
    @classmethod
    def reload(cls):
        """重新載入所有配置"""
        cls._app_config = None
        cls._model_config = None
        cls._languages_config = None
        cls._languages_list = None
        logger.info("已重新載入所有配置")
