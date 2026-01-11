# 資料模型：多國語言翻譯系統

**功能分支**: `001-multilang-translation`  
**建立日期**: 2026-01-11  
**狀態**: 完成

## 概述

本文件定義多國語言翻譯系統的資料模型，包含後端服務實體與前端狀態結構。系統不使用傳統資料庫，所有資料均存於記憶體或瀏覽器 sessionStorage。

---

## 後端實體（Python/Django）

### 1. Language（語言）

代表系統支援的翻譯語言。定義於 `config/languages.yaml`。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| code | str | ✅ | 語言代碼，如 "zh-TW", "en" |
| name | str | ✅ | 本地名稱，如 "繁體中文" |
| name_en | str | ✅ | 英文名稱，如 "Traditional Chinese" |
| is_enabled | bool | ✅ | 是否啟用 |
| sort_order | int | ✅ | 顯示排序 |

**支援的語言清單**：
| code | name | name_en |
|------|------|---------|
| zh-TW | 繁體中文 | Traditional Chinese |
| zh-CN | 簡體中文 | Simplified Chinese |
| en | 英文 | English |
| ja | 日文 | Japanese |
| ko | 韓文 | Korean |
| fr | 法文 | French |
| de | 德文 | German |
| es | 西班牙文 | Spanish |

**Python 資料類別**：
```python
from dataclasses import dataclass

@dataclass
class Language:
    code: str
    name: str
    name_en: str
    is_enabled: bool = True
    sort_order: int = 0
```

---

### 2. TranslationRequest（翻譯請求）

代表一次翻譯操作的輸入。

| 欄位 | 型別 | 必填 | 驗證規則 | 說明 |
|------|------|------|----------|------|
| request_id | str (UUID) | ✅ | 自動生成 | 唯一識別碼 |
| text | str | ✅ | 1-10,000 字元 | 原文內容 |
| source_language | str | ✅ | 有效語言代碼或 "auto" | 來源語言 |
| target_language | str | ✅ | 有效語言代碼 | 目標語言 |
| quality | str | ✅ | fast/standard/high | 翻譯品質 |
| client_ip | str | ✅ | - | 請求來源 IP |
| received_at | datetime | ✅ | 自動設定 | 請求接收時間 |

**驗證規則**：
- text 不得為空白或僅含空白字元
- source_language ≠ target_language（除非 source_language = "auto"）
- quality 預設為 "standard"

**Python 資料類別**：
```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

@dataclass
class TranslationRequest:
    text: str
    target_language: str
    source_language: str = "auto"
    quality: str = "standard"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    client_ip: str = ""
    received_at: datetime = field(default_factory=datetime.utcnow)
```

---

### 3. TranslationResponse（翻譯回應）

代表翻譯結果。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| request_id | str | ✅ | 對應的請求 ID |
| status | str | ✅ | 處理狀態 |
| translated_text | str | ❌ | 翻譯結果（成功時） |
| detected_language | str | ❌ | 偵測到的語言（自動偵測時） |
| confidence_score | float | ❌ | 語言偵測信心分數 (0.0-1.0) |
| processing_time_ms | int | ✅ | 處理時間（毫秒） |
| execution_mode | str | ✅ | 執行模式 ("gpu"/"cpu") |
| error_code | str | ❌ | 錯誤代碼（失敗時） |
| error_message | str | ❌ | 錯誤訊息（失敗時） |
| completed_at | datetime | ✅ | 完成時間 |

**Python 資料類別**：
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TranslationResponse:
    request_id: str
    status: str  # pending, processing, completed, failed, timeout, rejected
    processing_time_ms: int
    execution_mode: str  # gpu, cpu
    completed_at: datetime = field(default_factory=datetime.utcnow)
    translated_text: Optional[str] = None
    detected_language: Optional[str] = None
    confidence_score: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
```

---

### 4. QueueItem（佇列項目）

代表佇列中的請求。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| request_id | str | ✅ | 唯一識別碼 |
| request | TranslationRequest | ✅ | 翻譯請求物件 |
| status | str | ✅ | 佇列狀態 |
| queued_at | datetime | ✅ | 加入佇列時間 |
| started_at | datetime | ❌ | 開始處理時間 |
| queue_position | int | ❌ | 佇列位置（等待中時） |

**Python 資料類別**：
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class QueueItem:
    request_id: str
    request: TranslationRequest
    status: str  # queued, processing, completed, cancelled
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    queue_position: Optional[int] = None
```

---

### 5. SystemStatus（系統狀態）

代表系統監控資訊。

| 欄位 | 型別 | 說明 |
|------|------|------|
| is_running | bool | 系統是否運行中 |
| model_status | str | 模型狀態 (not_loaded/loading/loaded/error) |
| execution_mode | str | 當前執行模式 (gpu/cpu) |
| active_requests | int | 處理中的請求數 |
| queued_requests | int | 等待中的請求數 |
| max_concurrency | int | 最大並發數 (100) |
| max_queue_size | int | 最大佇列容量 (100) |
| memory_usage_mb | float | 記憶體使用量 (MB) |
| cpu_usage_percent | float | CPU 使用率 (%) |
| gpu_memory_usage_mb | float | GPU 記憶體使用量 (MB)，無 GPU 時為 None |
| uptime_seconds | int | 系統執行時間（秒） |
| last_updated | datetime | 最後更新時間 |

**Python 資料類別**：
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SystemStatus:
    is_running: bool
    model_status: str
    execution_mode: str
    active_requests: int
    queued_requests: int
    max_concurrency: int
    max_queue_size: int
    memory_usage_mb: float
    cpu_usage_percent: float
    uptime_seconds: int
    last_updated: datetime
    gpu_memory_usage_mb: Optional[float] = None
```

---

### 6. TranslationStatistics（翻譯統計）

代表 24 小時內的翻譯統計。

| 欄位 | 型別 | 說明 |
|------|------|------|
| period_start | datetime | 統計期間開始時間 |
| period_end | datetime | 統計期間結束時間 |
| total_requests | int | 總請求數 |
| successful_requests | int | 成功請求數 |
| failed_requests | int | 失敗請求數 |
| success_rate | float | 成功率 (%) |
| average_processing_time_ms | float | 平均處理時間（毫秒） |

**Python 資料類別**：
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TranslationStatistics:
    period_start: datetime
    period_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    average_processing_time_ms: float
```

#### MinuteSnapshot（分鐘快照）

用於統計滑動視窗的內部結構。

| 欄位 | 型別 | 說明 |
|------|------|------|
| timestamp | str | 時間戳（格式：YYYYMMDDHHMM） |
| total | int | 該分鐘請求數 |
| success | int | 該分鐘成功數 |
| total_time_ms | int | 該分鐘總處理時間 |

---

## 列舉值定義

### QualityMode（品質模式）
```python
class QualityMode:
    FAST = "fast"        # 快速
    STANDARD = "standard"  # 標準（預設）
    HIGH = "high"        # 高品質
```

### TranslationStatus（翻譯狀態）
```python
class TranslationStatus:
    PENDING = "pending"      # 等待中
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"   # 完成
    FAILED = "failed"        # 失敗
    TIMEOUT = "timeout"      # 逾時
    REJECTED = "rejected"    # 拒絕（佇列已滿）
```

### QueueStatus（佇列狀態）
```python
class QueueStatus:
    QUEUED = "queued"        # 佇列中等待
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"   # 完成
    CANCELLED = "cancelled"   # 取消
```

### ExecutionMode（執行模式）
```python
class ExecutionMode:
    GPU = "gpu"  # GPU 模式
    CPU = "cpu"  # CPU 模式（降級）
```

### ModelStatus（模型狀態）
```python
class ModelStatus:
    NOT_LOADED = "not_loaded"  # 未載入
    LOADING = "loading"       # 載入中
    LOADED = "loaded"         # 已載入
    ERROR = "error"           # 錯誤
```

---

## 前端狀態（sessionStorage）

### 1. UserSettings（使用者設定）

儲存於 sessionStorage，key: `userSettings`

| 欄位 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| quality | string | "standard" | 翻譯品質 ("fast"/"standard"/"high") |
| theme | string | "light" | 介面主題 ("light"/"dark") |
| fontSize | string | "medium" | 字體大小 ("small"/"medium"/"large") |
| defaultSourceLang | string | "auto" | 預設來源語言 |
| defaultTargetLang | string | "zh-TW" | 預設目標語言 |

**JSON 範例**：
```json
{
  "quality": "standard",
  "theme": "light",
  "fontSize": "medium",
  "defaultSourceLang": "auto",
  "defaultTargetLang": "zh-TW"
}
```

---

### 2. TranslationHistoryItem（翻譯歷史項目）

儲存於 sessionStorage，key: `translationHistory`，最多 20 筆。

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | string | UUID |
| originalText | string | 原文預覽（前 50 字元） |
| translatedText | string | 譯文預覽（前 50 字元） |
| fullOriginalText | string | 完整原文 |
| fullTranslatedText | string | 完整譯文 |
| sourceLang | string | 來源語言代碼 |
| targetLang | string | 目標語言代碼 |
| detectedLang | string | 偵測到的語言（若為自動偵測） |
| timestamp | string | ISO 8601 時間戳 |

**JSON 範例**：
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "originalText": "Hello, how are you today?...",
    "translatedText": "你好，今天好嗎？...",
    "fullOriginalText": "Hello, how are you today?",
    "fullTranslatedText": "你好，今天好嗎？",
    "sourceLang": "en",
    "targetLang": "zh-TW",
    "detectedLang": null,
    "timestamp": "2026-01-11T10:30:00.000Z"
  }
]
```

---

## 錯誤代碼定義

| 代碼 | 說明 | HTTP Status |
|------|------|-------------|
| VALIDATION_EMPTY_TEXT | 原文為空 | 400 |
| VALIDATION_TEXT_TOO_LONG | 超過 10,000 字元 | 400 |
| VALIDATION_SAME_LANGUAGE | 來源與目標語言相同 | 400 |
| VALIDATION_INVALID_LANGUAGE | 無效的語言代碼 | 400 |
| QUEUE_FULL | 請求佇列已滿 | 503 |
| SERVICE_UNAVAILABLE | 翻譯服務無法使用 | 503 |
| TRANSLATION_TIMEOUT | 翻譯逾時 | 504 |
| MODEL_NOT_LOADED | 模型未載入 | 503 |
| INTERNAL_ERROR | 內部錯誤 | 500 |

---

## 狀態轉換圖

### 翻譯請求狀態流轉

```
                         ┌──────────────┐
                         │   Received   │
                         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
            ┌───────────┐ ┌──────────┐ ┌──────────┐
            │  Rejected │ │  Queued  │ │Processing│
            │ (佇列滿)  │ │ (等待中) │ │ (直接)   │
            └───────────┘ └────┬─────┘ └────┬─────┘
                               │            │
                               ▼            │
                         ┌──────────┐       │
                         │Processing│◄──────┘
                         └────┬─────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
            ┌───────────┐ ┌───────┐ ┌───────┐
            │ Completed │ │Failed │ │Timeout│
            └───────────┘ └───────┘ └───────┘
```

---

## 資料保留策略

| 資料類型 | 儲存位置 | 保留期限 |
|----------|----------|----------|
| 翻譯請求/回應 | Django Cache | 請求完成後即清除 |
| 統計資料 | Django Cache | 24 小時滑動視窗 |
| 使用者設定 | 瀏覽器 sessionStorage | 標籤頁關閉即清除 |
| 翻譯歷史 | 瀏覽器 sessionStorage | 標籤頁關閉即清除 |
| 應用程式日誌 | 檔案系統 (logs/) | 30 天 |
| 翻譯請求日誌 | 檔案系統 (logs/) | 30 天 |
