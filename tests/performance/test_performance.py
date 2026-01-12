"""
效能測試 - 翻譯系統

測試系統在高負載下的表現
"""

import asyncio
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import unittest

import sys
import os

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../translation_project'))


class PerformanceTestResult:
    """效能測試結果"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.errors: List[str] = []
    
    def add_success(self, response_time: float):
        """記錄成功請求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.response_times.append(response_time)
    
    def add_failure(self, error: str):
        """記錄失敗請求"""
        self.total_requests += 1
        self.failed_requests += 1
        self.errors.append(error)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0
        return self.successful_requests / self.total_requests * 100
    
    @property
    def avg_response_time(self) -> float:
        """平均回應時間"""
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        """95 百分位回應時間"""
        if not self.response_times:
            return 0
        return statistics.quantiles(self.response_times, n=20)[18]
    
    @property
    def p99_response_time(self) -> float:
        """99 百分位回應時間"""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def summary(self) -> Dict:
        """取得摘要"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{self.success_rate:.2f}%",
            'avg_response_time_ms': f"{self.avg_response_time:.2f}",
            'p95_response_time_ms': f"{self.p95_response_time:.2f}" if self.response_times else "N/A",
            'p99_response_time_ms': f"{self.p99_response_time:.2f}" if self.response_times else "N/A",
            'min_response_time_ms': f"{min(self.response_times):.2f}" if self.response_times else "N/A",
            'max_response_time_ms': f"{max(self.response_times):.2f}" if self.response_times else "N/A",
        }


class TranslationPerformanceTest:
    """翻譯系統效能測試"""
    
    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
    
    def run_health_check_test(
        self, 
        num_requests: int = 100, 
        concurrency: int = 10
    ) -> PerformanceTestResult:
        """
        執行健康檢查 API 效能測試
        
        Args:
            num_requests: 總請求數
            concurrency: 並發數
        
        Returns:
            PerformanceTestResult: 測試結果
        """
        import requests
        
        result = PerformanceTestResult()
        url = f"{self.base_url}/api/health/"
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(url, timeout=10)
                elapsed = (time.time() - start_time) * 1000  # 毫秒
                
                if response.status_code == 200:
                    return ('success', elapsed)
                else:
                    return ('failure', f"HTTP {response.status_code}")
            except Exception as e:
                return ('failure', str(e))
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                status, data = future.result()
                if status == 'success':
                    result.add_success(data)
                else:
                    result.add_failure(data)
        
        return result
    
    def run_languages_api_test(
        self,
        num_requests: int = 100,
        concurrency: int = 10
    ) -> PerformanceTestResult:
        """
        執行語言 API 效能測試
        
        Args:
            num_requests: 總請求數
            concurrency: 並發數
        
        Returns:
            PerformanceTestResult: 測試結果
        """
        import requests
        
        result = PerformanceTestResult()
        url = f"{self.base_url}/api/v1/languages/"
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.get(url, timeout=10)
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return ('success', elapsed)
                else:
                    return ('failure', f"HTTP {response.status_code}")
            except Exception as e:
                return ('failure', str(e))
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                status, data = future.result()
                if status == 'success':
                    result.add_success(data)
                else:
                    result.add_failure(data)
        
        return result
    
    def run_translation_test(
        self,
        num_requests: int = 10,
        concurrency: int = 2,
        text: str = "Hello, world!"
    ) -> PerformanceTestResult:
        """
        執行翻譯 API 效能測試
        
        Args:
            num_requests: 總請求數
            concurrency: 並發數
            text: 翻譯文字
        
        Returns:
            PerformanceTestResult: 測試結果
        """
        import requests
        
        result = PerformanceTestResult()
        url = f"{self.base_url}/api/v1/translate/"
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.post(
                    url,
                    json={
                        'text': text,
                        'source_language': 'auto',
                        'target_language': 'zh-TW'
                    },
                    timeout=120
                )
                elapsed = (time.time() - start_time) * 1000
                
                if response.status_code in [200, 202]:
                    return ('success', elapsed)
                else:
                    return ('failure', f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                return ('failure', str(e))
        
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                status, data = future.result()
                if status == 'success':
                    result.add_success(data)
                else:
                    result.add_failure(data)
        
        return result


class TestPerformance(unittest.TestCase):
    """效能測試案例"""
    
    @unittest.skip("需要伺服器運行")
    def test_health_check_performance(self):
        """測試健康檢查效能"""
        tester = TranslationPerformanceTest()
        result = tester.run_health_check_test(
            num_requests=100,
            concurrency=10
        )
        
        print("\n健康檢查 API 效能測試結果:")
        for key, value in result.summary().items():
            print(f"  {key}: {value}")
        
        # 驗證成功率
        self.assertGreater(result.success_rate, 95)
        # 驗證平均回應時間
        self.assertLess(result.avg_response_time, 100)  # 100ms
    
    @unittest.skip("需要伺服器運行")
    def test_languages_api_performance(self):
        """測試語言 API 效能"""
        tester = TranslationPerformanceTest()
        result = tester.run_languages_api_test(
            num_requests=100,
            concurrency=10
        )
        
        print("\n語言 API 效能測試結果:")
        for key, value in result.summary().items():
            print(f"  {key}: {value}")
        
        self.assertGreater(result.success_rate, 95)
    
    @unittest.skip("需要伺服器運行和模型載入")
    def test_translation_performance(self):
        """測試翻譯效能"""
        tester = TranslationPerformanceTest()
        result = tester.run_translation_test(
            num_requests=10,
            concurrency=2,
            text="Hello, how are you today?"
        )
        
        print("\n翻譯 API 效能測試結果:")
        for key, value in result.summary().items():
            print(f"  {key}: {value}")
        
        self.assertGreater(result.success_rate, 80)


def run_benchmark():
    """執行基準測試（獨立執行）"""
    print("=" * 60)
    print("多國語言翻譯系統效能基準測試")
    print("=" * 60)
    
    tester = TranslationPerformanceTest()
    
    # 健康檢查測試
    print("\n1. 健康檢查 API (100 請求, 10 並發)")
    try:
        result = tester.run_health_check_test(100, 10)
        for key, value in result.summary().items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   錯誤: {e}")
    
    # 語言 API 測試
    print("\n2. 語言 API (100 請求, 10 並發)")
    try:
        result = tester.run_languages_api_test(100, 10)
        for key, value in result.summary().items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"   錯誤: {e}")
    
    print("\n" + "=" * 60)
    print("基準測試完成")
    print("=" * 60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='效能測試')
    parser.add_argument('--benchmark', action='store_true', help='執行基準測試')
    args = parser.parse_args()
    
    if args.benchmark:
        run_benchmark()
    else:
        unittest.main()
