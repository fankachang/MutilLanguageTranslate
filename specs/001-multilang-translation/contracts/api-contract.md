# API 契約：多國語言翻譯系統

**功能分支**: `001-multilang-translation`  
**建立日期**: 2026-01-11  
**API 版本**: v1

## 概述

本文件定義多國語言翻譯系統的 REST API 契約，基於 Django 4.2+ 實現。

---

## 基礎資訊

- **Base URL**: `http://{host}:8000/api/v1`
- **Content-Type**: `application/json`
- **字元編碼**: UTF-8

---

## API 端點

### 1. 翻譯 API

#### POST /api/v1/translate/

執行文字翻譯。

**請求**
```json
{
  "text": "Hello, how are you today?",
  "source_language": "en",
  "target_language": "zh-TW",
  "quality": "standard"
}
```

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| text | string | ✅ | 待翻譯文字（1-10,000 字元） |
| source_language | string | ❌ | 來源語言代碼或 "auto"（預設 "auto"） |
| target_language | string | ✅ | 目標語言代碼 |
| quality | string | ❌ | 品質模式（預設 "standard"） |

**成功回應** (200 OK)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "translated_text": "你好，今天好嗎？",
  "detected_language": "en",
  "confidence_score": 0.95,
  "processing_time_ms": 1250,
  "execution_mode": "gpu"
}
```

**排隊回應** (202 Accepted)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "queue_position": 5,
  "estimated_wait_seconds": 30
}
```

**錯誤回應** (4xx/5xx)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": {
    "code": "VALIDATION_TEXT_TOO_LONG",
    "message": "文字長度超過 10,000 字元，請縮短後再試"
  }
}
```

---

#### GET /api/v1/translate/{request_id}/status/

查詢翻譯請求狀態。

**路徑參數**
| 參數 | 型別 | 說明 |
|------|------|------|
| request_id | string (UUID) | 請求唯一識別碼 |

**回應** (200 OK)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "queue_position": null,
  "started_at": "2026-01-11T10:30:00Z"
}
```

---

### 2. 語言 API

#### GET /api/v1/languages/

取得支援的語言清單。

**回應** (200 OK)
```json
{
  "languages": [
    {
      "code": "zh-TW",
      "name": "繁體中文",
      "name_en": "Traditional Chinese",
      "is_enabled": true
    },
    {
      "code": "zh-CN",
      "name": "簡體中文",
      "name_en": "Simplified Chinese",
      "is_enabled": true
    },
    {
      "code": "en",
      "name": "英文",
      "name_en": "English",
      "is_enabled": true
    },
    {
      "code": "ja",
      "name": "日文",
      "name_en": "Japanese",
      "is_enabled": true
    },
    {
      "code": "ko",
      "name": "韓文",
      "name_en": "Korean",
      "is_enabled": true
    },
    {
      "code": "fr",
      "name": "法文",
      "name_en": "French",
      "is_enabled": true
    },
    {
      "code": "de",
      "name": "德文",
      "name_en": "German",
      "is_enabled": true
    },
    {
      "code": "es",
      "name": "西班牙文",
      "name_en": "Spanish",
      "is_enabled": true
    }
  ],
  "default_source_language": "auto",
  "default_target_language": "zh-TW"
}
```

---

### 3. 系統監控 API

#### GET /api/v1/admin/status/

取得系統狀態（需 IP 白名單）。

**回應** (200 OK)
```json
{
  "system": {
    "is_running": true,
    "uptime": "02:15:30",
    "last_updated": "2026-01-11T10:30:00Z"
  },
  "model": {
    "status": "loaded",
    "name": "TAIDE-LX-7B",
    "execution_mode": "gpu"
  },
  "resources": {
    "memory_usage_mb": 4096,
    "cpu_usage_percent": 25.5,
    "gpu_memory_usage_mb": 8192
  },
  "queue": {
    "active_requests": 12,
    "queued_requests": 5,
    "max_concurrency": 100,
    "max_queue_size": 100
  }
}
```

**未授權回應** (403 Forbidden)
```json
{
  "error": {
    "code": "ACCESS_DENIED",
    "message": "IP 位址不在白名單中"
  }
}
```

---

#### GET /api/v1/admin/statistics/

取得翻譯統計（需 IP 白名單）。

**回應** (200 OK)
```json
{
  "period": {
    "start": "2026-01-10T10:30:00Z",
    "end": "2026-01-11T10:30:00Z"
  },
  "summary": {
    "total_requests": 1250,
    "successful_requests": 1200,
    "failed_requests": 50,
    "success_rate": 96.0,
    "average_processing_time_ms": 2150
  },
  "hourly_breakdown": [
    {
      "hour": "2026-01-11T10:00:00Z",
      "requests": 45,
      "success_rate": 97.8,
      "avg_processing_time_ms": 2050
    }
  ]
}
```

---

### 4. 健康檢查 API

#### GET /api/health/

健康檢查端點。

**健康回應** (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2026-01-11T10:30:00Z",
  "checks": {
    "api": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "translation_model": {
      "status": "healthy",
      "model_name": "TAIDE-LX-7B",
      "execution_mode": "gpu",
      "last_check_time": "2026-01-11T10:29:55Z"
    }
  }
}
```

**不健康回應** (503 Service Unavailable)
```json
{
  "status": "unhealthy",
  "timestamp": "2026-01-11T10:30:00Z",
  "checks": {
    "api": {
      "status": "healthy",
      "response_time_ms": 2
    },
    "translation_model": {
      "status": "unhealthy",
      "error": "Model not loaded"
    }
  }
}
```

---

## 錯誤代碼對照表

| 代碼 | HTTP Status | 中文訊息 |
|------|-------------|----------|
| VALIDATION_EMPTY_TEXT | 400 | 請輸入要翻譯的文字 |
| VALIDATION_TEXT_TOO_LONG | 400 | 文字長度超過 10,000 字元，請縮短後再試 |
| VALIDATION_SAME_LANGUAGE | 400 | 來源語言與目標語言不可相同 |
| VALIDATION_INVALID_LANGUAGE | 400 | 無效的語言代碼 |
| QUEUE_FULL | 503 | 系統繁忙，請稍後再試 |
| SERVICE_UNAVAILABLE | 503 | 翻譯服務暫時無法使用，請稍後再試 |
| TRANSLATION_TIMEOUT | 504 | 翻譯逾時，請嘗試縮短文字長度或稍後再試 |
| MODEL_NOT_LOADED | 503 | 翻譯模型尚未載入，請稍後再試 |
| NETWORK_ERROR | 503 | 網路連線失敗，請檢查網路狀態 |
| ACCESS_DENIED | 403 | IP 位址不在白名單中 |
| INTERNAL_ERROR | 500 | 系統內部錯誤，請聯繫管理員 |

---

## 請求標頭

### 必要標頭
| 標頭 | 值 | 說明 |
|------|-----|------|
| Content-Type | application/json | 請求內容類型 |

### 可選標頭
| 標頭 | 說明 |
|------|------|
| X-Request-ID | 客戶端提供的請求追蹤 ID |

---

## 回應標頭

| 標頭 | 說明 |
|------|------|
| X-Request-ID | 請求唯一識別碼 |
| X-Processing-Time-Ms | 處理時間（毫秒） |

---

## Django URL 配置

```python
# translator/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.translate, name='translate'),
    path('translate/<uuid:request_id>/status/', views.translate_status, name='translate_status'),
    path('languages/', views.languages, name='languages'),
    path('admin/status/', views.admin_status, name='admin_status'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),
]

# translation_project/urls.py
from django.urls import path, include
from translator.api.views import health_check

urlpatterns = [
    path('api/v1/', include('translator.api.urls')),
    path('api/health/', health_check, name='health_check'),
]
```
