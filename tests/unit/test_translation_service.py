"""
單元測試 - 翻譯服務

測試 TranslationService 的核心功能
"""

import unittest
from unittest.mock import MagicMock, patch

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../translation_project'))

from translator.enums import QualityMode, TranslationStatus


class TestQualityMode(unittest.TestCase):
    """測試品質模式列舉"""
    
    def test_valid_quality_modes(self):
        """測試有效的品質模式"""
        self.assertTrue(QualityMode.is_valid('standard'))
        self.assertTrue(QualityMode.is_valid('high'))
    
    def test_invalid_quality_mode(self):
        """測試無效的品質模式"""
        self.assertFalse(QualityMode.is_valid('invalid'))
        self.assertFalse(QualityMode.is_valid(''))
        self.assertFalse(QualityMode.is_valid(None))


class TestTranslationStatus(unittest.TestCase):
    """測試翻譯狀態列舉"""
    
    def test_status_values(self):
        """測試狀態值"""
        self.assertEqual(TranslationStatus.PENDING, 'pending')
        self.assertEqual(TranslationStatus.PROCESSING, 'processing')
        self.assertEqual(TranslationStatus.COMPLETED, 'completed')
        self.assertEqual(TranslationStatus.FAILED, 'failed')


class TestTranslationRequest(unittest.TestCase):
    """測試翻譯請求模型"""
    
    def test_create_request(self):
        """測試建立翻譯請求"""
        from translator.models import TranslationRequest
        
        request = TranslationRequest(
            text='Hello',
            source_language='en',
            target_language='zh-TW',
            quality='standard',
            client_ip='127.0.0.1'
        )
        
        self.assertEqual(request.text, 'Hello')
        self.assertEqual(request.source_language, 'en')
        self.assertEqual(request.target_language, 'zh-TW')
        self.assertEqual(request.quality, 'standard')
        self.assertEqual(request.client_ip, '127.0.0.1')
        self.assertIsNotNone(request.request_id)
        self.assertIsNotNone(request.created_at)
    
    def test_text_length_validation(self):
        """測試文字長度驗證"""
        from translator.models import TranslationRequest
        
        # 短文字應該通過
        request = TranslationRequest(
            text='Short text',
            source_language='auto',
            target_language='en',
            quality='standard',
            client_ip='127.0.0.1'
        )
        self.assertIsNotNone(request.request_id)


class TestTranslationResponse(unittest.TestCase):
    """測試翻譯回應模型"""
    
    def test_successful_response(self):
        """測試成功的翻譯回應"""
        from translator.models import TranslationResponse
        
        response = TranslationResponse(
            request_id='test-123',
            status=TranslationStatus.COMPLETED,
            translated_text='你好',
            processing_time_ms=100.5,
            execution_mode='cpu'
        )
        
        self.assertEqual(response.request_id, 'test-123')
        self.assertEqual(response.status, TranslationStatus.COMPLETED)
        self.assertEqual(response.translated_text, '你好')
        self.assertEqual(response.processing_time_ms, 100.5)
        self.assertEqual(response.execution_mode, 'cpu')
    
    def test_failed_response(self):
        """測試失敗的翻譯回應"""
        from translator.models import TranslationResponse
        
        response = TranslationResponse(
            request_id='test-456',
            status=TranslationStatus.FAILED,
            processing_time_ms=0,
            execution_mode='cpu',
            error_code='VALIDATION_TEXT_TOO_LONG',
            error_message='文字超過長度限制'
        )
        
        self.assertEqual(response.status, TranslationStatus.FAILED)
        self.assertEqual(response.error_code, 'VALIDATION_TEXT_TOO_LONG')
        self.assertIsNone(response.translated_text)


if __name__ == '__main__':
    unittest.main()
