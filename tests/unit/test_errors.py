"""
單元測試 - 錯誤處理

測試錯誤代碼和錯誤訊息
"""

import unittest

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../translation_project'))


class TestErrorCode(unittest.TestCase):
    """測試錯誤代碼"""
    
    def test_error_code_constants(self):
        """測試錯誤代碼常數"""
        from translator.errors import ErrorCode
        
        # 驗證錯誤應該存在
        self.assertIsNotNone(ErrorCode.VALIDATION_EMPTY_TEXT)
        self.assertIsNotNone(ErrorCode.VALIDATION_TEXT_TOO_LONG)
        self.assertIsNotNone(ErrorCode.VALIDATION_INVALID_LANGUAGE)
        
        # 服務錯誤應該存在
        self.assertIsNotNone(ErrorCode.SERVICE_UNAVAILABLE)
        self.assertIsNotNone(ErrorCode.MODEL_NOT_LOADED)
        
        # 內部錯誤應該存在
        self.assertIsNotNone(ErrorCode.INTERNAL_ERROR)


class TestGetErrorMessage(unittest.TestCase):
    """測試取得錯誤訊息"""
    
    def test_get_validation_error_message(self):
        """測試取得驗證錯誤訊息"""
        from translator.errors import ErrorCode, get_error_message
        
        message = get_error_message(ErrorCode.VALIDATION_EMPTY_TEXT)
        
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_get_unknown_error_message(self):
        """測試取得未知錯誤訊息"""
        from translator.errors import get_error_message
        
        message = get_error_message('UNKNOWN_CODE')
        
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)


class TestGetHttpStatus(unittest.TestCase):
    """測試取得 HTTP 狀態碼"""
    
    def test_validation_error_status(self):
        """測試驗證錯誤狀態碼"""
        from translator.errors import ErrorCode, get_http_status
        
        status = get_http_status(ErrorCode.VALIDATION_EMPTY_TEXT)
        self.assertEqual(status, 400)
    
    def test_service_error_status(self):
        """測試服務錯誤狀態碼"""
        from translator.errors import ErrorCode, get_http_status
        
        status = get_http_status(ErrorCode.SERVICE_UNAVAILABLE)
        self.assertEqual(status, 503)
    
    def test_internal_error_status(self):
        """測試內部錯誤狀態碼"""
        from translator.errors import ErrorCode, get_http_status
        
        status = get_http_status(ErrorCode.INTERNAL_ERROR)
        self.assertEqual(status, 500)


class TestTranslationError(unittest.TestCase):
    """測試翻譯例外類別"""
    
    def test_create_translation_error(self):
        """測試建立翻譯例外"""
        from translator.errors import TranslationError, ErrorCode
        
        error = TranslationError(
            code=ErrorCode.VALIDATION_EMPTY_TEXT,
            message='測試錯誤訊息'
        )
        
        self.assertEqual(error.code, ErrorCode.VALIDATION_EMPTY_TEXT)
        self.assertEqual(error.message, '測試錯誤訊息')
        self.assertEqual(error.http_status, 400)
    
    def test_translation_error_str(self):
        """測試翻譯例外字串表示"""
        from translator.errors import TranslationError, ErrorCode
        
        error = TranslationError(
            code=ErrorCode.VALIDATION_EMPTY_TEXT,
            message='測試訊息'
        )
        
        error_str = str(error)
        self.assertIn(ErrorCode.VALIDATION_EMPTY_TEXT, error_str)
        self.assertIn('測試訊息', error_str)


if __name__ == '__main__':
    unittest.main()
