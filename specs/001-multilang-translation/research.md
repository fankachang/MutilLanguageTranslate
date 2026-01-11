# 研究文件：多國語言翻譯系統

**功能分支**: `001-multilang-translation`  
**建立日期**: 2026-01-11  
**狀態**: 完成

## 研究摘要

本文件記錄多國語言翻譯系統開發過程中的技術研究結果，包含架構決策、技術選型、最佳實踐等。

---

## 1. Django ASGI 與非同步處理

### 決策
採用 Django 4.2+ 搭配 ASGI 支援，使用 uvicorn 作為 ASGI 伺服器。

### 理由
1. **非同步支援**：ASGI 允許非同步視圖，適合處理長時間執行的翻譯請求
2. **Constitution 一致**：Django 4.2+ 是 Constitution 指定的技術棧
3. **並發處理**：搭配 async views 可更有效處理 100 並發使用者

### 配置範例
```python
# asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'translation_project.settings')
application = get_asgi_application()
```

```bash
# 啟動方式
uvicorn translation_project.asgi:application --host 0.0.0.0 --port 8000
```

### 考慮但未採用的替代方案
| 方案 | 未採用原因 |
|------|-----------|
| FastAPI | 不符合 Constitution 指定的 Django 技術棧 |
| Flask | 缺乏內建的 ORM 和 Admin，且 Constitution 明確指定 Django |
| Celery 非同步任務 | 增加架構複雜度，單體應用內直接使用 async 更簡單 |

---

## 2. TAIDE-LX-7B 模型載入與推論

### 決策
直接在 Django 應用內載入模型，使用 transformers 庫進行推論。

### 技術細節

#### 模型載入（model_service.py）
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class ModelService:
    _instance = None
    _model = None
    _tokenizer = None
    _device = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._load_model()
        return cls._instance
    
    @classmethod
    def _load_model(cls):
        model_path = "models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979"
        
        # 偵測 GPU 可用性
        if torch.cuda.is_available():
            cls._device = "cuda"
            cls._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                max_memory={0: "12GiB"}
            )
        else:
            cls._device = "cpu"
            cls._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
        
        cls._tokenizer = AutoTokenizer.from_pretrained(model_path)
```

#### 生成參數（品質模式）
| 模式 | temperature | top_p | num_beams | max_new_tokens |
|------|-------------|-------|-----------|----------------|
| 快速 | 0.7 | 0.9 | 1 | 512 |
| 標準 | 0.5 | 0.85 | 2 | 1024 |
| 高品質 | 0.3 | 0.8 | 4 | 2048 |

### 理由
1. **簡化架構**：無需額外微服務，符合 Constitution「Simplicity and Pragmatism」原則
2. **單例模式**：模型只載入一次，避免重複載入的記憶體浪費
3. **自動降級**：偵測 GPU 不可用時自動切換至 CPU 模式

---

## 3. 並發請求處理與佇列機制

### 決策
使用 Django Cache Framework 搭配 threading.Lock 實現執行緒安全的請求管理。

### 架構設計

```python
import threading
from django.core.cache import cache

class QueueService:
    _lock = threading.Lock()
    _active_count = 0
    _queue = []
    
    MAX_CONCURRENT = 100
    MAX_QUEUE_SIZE = 100
    
    @classmethod
    def acquire_slot(cls, request_id):
        with cls._lock:
            if cls._active_count < cls.MAX_CONCURRENT:
                cls._active_count += 1
                return {"status": "processing"}
            elif len(cls._queue) < cls.MAX_QUEUE_SIZE:
                cls._queue.append(request_id)
                return {"status": "queued", "position": len(cls._queue)}
            else:
                return {"status": "rejected"}
    
    @classmethod
    def release_slot(cls, request_id):
        with cls._lock:
            cls._active_count -= 1
            # 處理等待佇列中的下一個請求
            if cls._queue:
                next_request = cls._queue.pop(0)
                cls._active_count += 1
                return next_request
        return None
```

### 請求狀態流轉
1. **Received** → 請求已接收
2. **Queued** → 等待處理（並發已滿）
3. **Processing** → 處理中
4. **Completed** → 完成
5. **Failed** → 失敗
6. **Rejected** → 拒絕（總請求超過 200）

### 理由
1. **threading.Lock**：Python 標準庫，無需額外依賴
2. **簡單有效**：單一伺服器部署場景下足夠使用
3. **符合 Constitution**：避免引入複雜的分散式佇列系統

---

## 4. Django Templates + HTMX + Alpine.js

### 決策
採用 Django Templates 作為模板引擎，搭配 HTMX 實現無刷新互動，Alpine.js 處理客戶端狀態。

### 技術考量

#### 為何選擇此組合
1. **Django Templates**：Django 內建，無需額外配置
2. **HTMX**：輕量級（14KB），透過 HTML 屬性實現 AJAX 互動
3. **Alpine.js**：輕量級（15KB），適合簡單的客戶端狀態管理

#### 範例：翻譯表單
```html
<!-- index.html -->
<form hx-post="/api/v1/translate/" 
      hx-target="#result" 
      hx-indicator="#loading"
      x-data="{ text: '', targetLang: 'zh-TW' }">
    
    <textarea name="text" 
              x-model="text"
              maxlength="10000"
              required></textarea>
    
    <select name="targetLanguage" x-model="targetLang">
        {% for lang in languages %}
        <option value="{{ lang.code }}">{{ lang.name }}</option>
        {% endfor %}
    </select>
    
    <button type="submit" 
            :disabled="!text.trim() || text.length > 10000">
        翻譯
    </button>
    
    <div id="loading" class="htmx-indicator">處理中...</div>
</form>

<div id="result"></div>
```

### 理由
1. **符合 Constitution**：明確要求「Server-rendered templates preferred over SPA」
2. **離線友好**：HTMX 和 Alpine.js 靜態檔案可本地託管
3. **低學習曲線**：團隊無需學習 React/Vue 等複雜框架

---

## 5. 語言偵測與翻譯 Prompt 設計

### 決策
使用 TAIDE-LX-7B 同時執行語言偵測與翻譯，透過精心設計的 Prompt 達成。

### Prompt 範本

#### 自動偵測模式
```
你是一個專業的翻譯助手。請先識別以下文字的語言，然後翻譯成{目標語言}。

原文：
{原文內容}

請以以下格式回覆：
偵測語言：[語言名稱]
信心分數：[0.0-1.0]
翻譯結果：
[翻譯內容]
```

#### 指定語言模式
```
你是一個專業的翻譯助手。請將以下{來源語言}文字翻譯成{目標語言}，保持原文的格式與段落結構。

原文：
{原文內容}

翻譯結果：
```

### 信心分數處理
- 分數 ≥ 0.5：使用偵測到的語言
- 分數 < 0.5：回退使用繁體中文（zh-TW）作為預設

### 理由
1. **單次推論**：減少延遲，避免兩次模型呼叫
2. **結構化輸出**：便於解析語言偵測結果
3. **保留格式**：明確要求保持段落結構

---

## 6. 統計資料滑動視窗實現

### 決策
使用 Django Cache Framework 實現記憶體內時間序列結構，每分鐘匯總一次，保留 24 小時資料。

### 資料結構

```python
import threading
from datetime import datetime, timedelta
from django.core.cache import cache

class StatisticsService:
    _lock = threading.Lock()
    CACHE_KEY_PREFIX = "translation_stats_"
    RETENTION_MINUTES = 24 * 60  # 24 小時
    
    @classmethod
    def record_request(cls, success: bool, processing_time_ms: int):
        """記錄一次翻譯請求"""
        now = datetime.utcnow()
        minute_key = now.strftime("%Y%m%d%H%M")
        cache_key = f"{cls.CACHE_KEY_PREFIX}{minute_key}"
        
        with cls._lock:
            stats = cache.get(cache_key, {
                "total": 0,
                "success": 0,
                "total_time_ms": 0,
                "timestamp": minute_key
            })
            
            stats["total"] += 1
            if success:
                stats["success"] += 1
            stats["total_time_ms"] += processing_time_ms
            
            cache.set(cache_key, stats, timeout=cls.RETENTION_MINUTES * 60)
    
    @classmethod
    def get_24h_statistics(cls):
        """取得近 24 小時統計"""
        now = datetime.utcnow()
        results = []
        
        for i in range(cls.RETENTION_MINUTES):
            minute = now - timedelta(minutes=i)
            minute_key = minute.strftime("%Y%m%d%H%M")
            cache_key = f"{cls.CACHE_KEY_PREFIX}{minute_key}"
            stats = cache.get(cache_key)
            if stats:
                results.append(stats)
        
        # 匯總統計
        total_requests = sum(s["total"] for s in results)
        successful_requests = sum(s["success"] for s in results)
        total_time = sum(s["total_time_ms"] for s in results)
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "average_processing_time_ms": (total_time / total_requests) if total_requests > 0 else 0
        }
```

### 理由
1. **Django Cache Framework**：Django 內建，支援多種後端（記憶體、檔案、Redis）
2. **記憶體效率**：24 小時 × 60 分鐘 = 1440 筆記錄，佔用極少記憶體
3. **自動過期**：cache.set 的 timeout 參數自動清理過期資料

---

## 7. IP 白名單與內網存取控制

### 決策
使用 Django Middleware 實現 IP 過濾，支援 CIDR 格式配置。

### 實現方式

```python
# middleware/ip_whitelist.py
import ipaddress
import yaml
from django.http import HttpResponseForbidden

class IpWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._load_config()
    
    def _load_config(self):
        with open("config/app_config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        self.internal_ranges = [
            ipaddress.ip_network(cidr, strict=False)
            for cidr in config.get("security", {}).get("internal_ip_ranges", [])
        ]
        self.admin_ranges = [
            ipaddress.ip_network(cidr, strict=False)
            for cidr in config.get("security", {}).get("admin_ip_ranges", [])
        ]
    
    def __call__(self, request):
        client_ip = self._get_client_ip(request)
        
        # 管理頁面需要 admin 白名單
        if request.path.startswith("/admin/status"):
            if not self._is_in_ranges(client_ip, self.admin_ranges):
                return HttpResponseForbidden("IP 位址不在白名單中")
        
        # 所有頁面需要內網 IP
        if not self._is_in_ranges(client_ip, self.internal_ranges):
            return HttpResponseForbidden("僅限內網存取")
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
    
    def _is_in_ranges(self, ip_str, ranges):
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in network for network in ranges)
        except ValueError:
            return False
```

### 配置範例 (config/app_config.yaml)
```yaml
security:
  internal_ip_ranges:
    - "192.168.0.0/16"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "127.0.0.1/32"
  admin_ip_ranges:
    - "192.168.1.100/32"
    - "192.168.1.101/32"
```

---

## 8. 日誌輪替與檔案管理

### 決策
使用 Python logging 模組搭配 RotatingFileHandler，由應用程式自行管理日誌輪替。

### 配置範例

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "app_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/app.log",
            "when": "midnight",
            "backupCount": 30,  # 保留 30 天
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "translation_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/translation.log",
            "when": "midnight",
            "backupCount": 30,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "translator": {
            "handlers": ["app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "translator.translation": {
            "handlers": ["translation_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
```

### 日誌分類
| 檔案 | 內容 | 層級 |
|------|------|------|
| logs/app.log | 程式錯誤、系統事件 | ERROR, WARNING, INFO |
| logs/translation.log | 翻譯請求記錄 | INFO |

---

## 9. 健康檢查端點設計

### 決策
實現 /api/health 端點，驗證 API 服務與翻譯模型狀態。

### 實現方式

```python
# api/views.py
from django.http import JsonResponse
from translator.services.model_service import ModelService
from datetime import datetime
import time

def health_check(request):
    start_time = time.time()
    
    checks = {
        "api": {"status": "healthy", "response_time_ms": 0},
        "translation_model": {"status": "unknown"}
    }
    
    # 檢查模型狀態
    try:
        model_service = ModelService.get_instance()
        if model_service.is_loaded():
            checks["translation_model"] = {
                "status": "healthy",
                "model_name": "TAIDE-LX-7B",
                "execution_mode": model_service.get_device(),
            }
        else:
            checks["translation_model"] = {
                "status": "unhealthy",
                "error": "Model not loaded"
            }
    except Exception as e:
        checks["translation_model"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    checks["api"]["response_time_ms"] = int((time.time() - start_time) * 1000)
    
    # 決定整體狀態
    overall_status = "healthy" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "unhealthy"
    
    status_code = 200 if overall_status == "healthy" else 503
    
    return JsonResponse({
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": checks
    }, status=status_code)
```

---

## 10. 前端 sessionStorage 資料結構

### 決策
使用瀏覽器 sessionStorage 儲存使用者設定與翻譯歷史，透過 Alpine.js 管理。

### 資料結構

#### 使用者設定 (key: "userSettings")
```json
{
  "quality": "standard",
  "theme": "light",
  "fontSize": "medium",
  "defaultSourceLang": "auto",
  "defaultTargetLang": "zh-TW"
}
```

#### 翻譯歷史 (key: "translationHistory")
```json
[
  {
    "id": "uuid-1234",
    "originalText": "Hello world...",
    "translatedText": "你好世界...",
    "sourceLang": "en",
    "targetLang": "zh-TW",
    "detectedLang": "en",
    "timestamp": "2026-01-11T10:30:00.000Z"
  }
]
```

### Alpine.js 實現範例
```html
<div x-data="settingsStore()" x-init="loadSettings()">
    <script>
        function settingsStore() {
            return {
                settings: {
                    quality: 'standard',
                    theme: 'light',
                    fontSize: 'medium'
                },
                loadSettings() {
                    const saved = sessionStorage.getItem('userSettings');
                    if (saved) {
                        this.settings = JSON.parse(saved);
                    }
                    this.applyTheme();
                },
                saveSettings() {
                    sessionStorage.setItem('userSettings', JSON.stringify(this.settings));
                    this.applyTheme();
                },
                applyTheme() {
                    document.documentElement.classList.toggle('dark', this.settings.theme === 'dark');
                }
            }
        }
    </script>
</div>
```

---

## 結論

本研究涵蓋了多國語言翻譯系統的關鍵技術決策，所有選擇均完全符合 Constitution 的核心原則：

1. ✅ **Offline-First**：無外部依賴，完全內網運作
2. ✅ **Performance**：明確的效能目標與實現路徑
3. ✅ **Simplicity**：Django 單體架構，無不必要的微服務
4. ✅ **Testability**：所有元件均可獨立測試
5. ✅ **Observability**：完整的日誌與監控機制
6. ✅ **Configuration**：YAML 配置檔案，所有參數可配置
7. ✅ **API-First**：明確的 API 契約設計

與先前 .NET 方案相比，Django 方案的優勢：
- **技術棧統一**：Python 全端，無需維護兩種語言
- **架構簡化**：單體應用，無微服務間通訊
- **Constitution 一致**：完全符合規定，無需偏差說明

下一步：進入 Phase 1，產出 data-model.md 與 contracts/。
