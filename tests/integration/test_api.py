"""
整合測試 - API 端點

測試 REST API 的完整請求/回應流程
"""

import json
import unittest

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../translation_project'))

# 設定 Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'translation_project.settings')

import django
django.setup()

from django.test import TestCase, Client


class TestHealthCheckAPI(TestCase):
    """測試健康檢查 API"""
    
    def setUp(self):
        """設定測試環境"""
        self.client = Client()
    
    def test_health_check_endpoint(self):
        """測試健康檢查端點"""
        response = self.client.get('/api/health/')
        
        # 應該回傳 200 或 503
        self.assertIn(response.status_code, [200, 503])
        
        # 應該回傳 JSON
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('checks', data)
    
    def test_readiness_probe(self):
        """測試就緒探針"""
        response = self.client.get('/api/ready/')
        
        # 應該回傳 200 或 503
        self.assertIn(response.status_code, [200, 503])
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
    
    def test_liveness_probe(self):
        """測試存活探針"""
        response = self.client.get('/api/live/')
        
        # 存活探針應該回傳 200（除非嚴重問題）
        self.assertIn(response.status_code, [200, 503])
        
        data = response.json()
        self.assertIn('status', data)


class TestLanguagesAPI(TestCase):
    """測試語言 API"""
    
    def setUp(self):
        """設定測試環境"""
        self.client = Client()
    
    def test_get_languages(self):
        """測試取得語言清單"""
        response = self.client.get('/api/v1/languages/')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('languages', data)
        self.assertIsInstance(data['languages'], list)
        self.assertGreater(len(data['languages']), 0)
        
        # 檢查語言結構
        for lang in data['languages']:
            self.assertIn('code', lang)
            self.assertIn('name', lang)
    
    def test_default_languages(self):
        """測試預設語言"""
        response = self.client.get('/api/v1/languages/')
        
        data = response.json()
        
        # 應該有預設來源和目標語言
        self.assertIn('default_source_language', data)
        self.assertIn('default_target_language', data)


class TestTranslateAPI(TestCase):
    """測試翻譯 API"""
    
    def setUp(self):
        """設定測試環境"""
        self.client = Client()
    
    def test_translate_missing_target_language(self):
        """測試缺少目標語言"""
        response = self.client.post(
            '/api/v1/translate/',
            data=json.dumps({
                'text': 'Hello',
                'source_language': 'en'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
    
    def test_translate_invalid_json(self):
        """測試無效的 JSON"""
        response = self.client.post(
            '/api/v1/translate/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertIn('error', data)
    
    def test_translate_empty_text(self):
        """測試空文字（應由服務層處理）"""
        response = self.client.post(
            '/api/v1/translate/',
            data=json.dumps({
                'text': '',
                'source_language': 'auto',
                'target_language': 'en'
            }),
            content_type='application/json'
        )
        
        # 可能是 400 或由服務處理
        self.assertIn(response.status_code, [200, 202, 400, 500, 503])


class TestPageRoutes(TestCase):
    """測試頁面路由"""
    
    def setUp(self):
        """設定測試環境"""
        self.client = Client()
    
    def test_index_page(self):
        """測試首頁"""
        response = self.client.get('/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '翻譯')
    
    def test_history_page(self):
        """測試歷史頁面"""
        response = self.client.get('/history/')
        
        self.assertEqual(response.status_code, 200)
    
    def test_settings_page(self):
        """測試設定頁面"""
        response = self.client.get('/settings/')
        
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
