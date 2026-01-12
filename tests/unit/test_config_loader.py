"""
單元測試 - 配置載入器

測試 ConfigLoader 的配置讀取功能
"""

import unittest
from unittest.mock import patch, mock_open
import yaml

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../translation_project'))


class TestConfigLoader(unittest.TestCase):
    """測試配置載入器"""
    
    def test_get_enabled_languages(self):
        """測試取得啟用的語言"""
        from translator.utils.config_loader import ConfigLoader
        
        languages = ConfigLoader.get_enabled_languages()
        
        # 應該至少有一些語言
        self.assertIsInstance(languages, list)
        self.assertGreater(len(languages), 0)
        
        # 每個語言應該有 code 和 name
        for lang in languages:
            self.assertTrue(hasattr(lang, 'code'))
            self.assertTrue(hasattr(lang, 'name'))
    
    def test_get_default_source_language(self):
        """測試取得預設來源語言"""
        from translator.utils.config_loader import ConfigLoader
        
        default_source = ConfigLoader.get_default_source_language()
        
        # 預設來源語言應該是 'auto'
        self.assertEqual(default_source, 'auto')
    
    def test_get_default_target_language(self):
        """測試取得預設目標語言"""
        from translator.utils.config_loader import ConfigLoader
        
        default_target = ConfigLoader.get_default_target_language()
        
        # 預設目標語言應該是有效的語言代碼
        self.assertIsInstance(default_target, str)
        self.assertGreater(len(default_target), 0)
    
    def test_is_language_supported(self):
        """測試檢查語言是否支援"""
        from translator.utils.config_loader import ConfigLoader
        
        # 英文應該被支援
        self.assertTrue(ConfigLoader.is_language_supported('en'))
        
        # 繁體中文應該被支援
        self.assertTrue(ConfigLoader.is_language_supported('zh-TW'))
        
        # 不存在的語言代碼
        self.assertFalse(ConfigLoader.is_language_supported('invalid-lang'))


class TestLanguageModel(unittest.TestCase):
    """測試語言模型類別"""
    
    def test_language_to_dict(self):
        """測試語言轉換為字典"""
        from translator.utils.config_loader import Language
        
        lang = Language(
            code='en',
            name='English',
            native_name='English',
            enabled=True
        )
        
        result = lang.to_dict()
        
        self.assertEqual(result['code'], 'en')
        self.assertEqual(result['name'], 'English')
        self.assertEqual(result['native_name'], 'English')
        self.assertTrue(result['enabled'])


if __name__ == '__main__':
    unittest.main()
