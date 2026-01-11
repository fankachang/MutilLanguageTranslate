# Implementation Plan: 多國語言翻譯系統

**Branch**: `001-multilang-translation` | **Date**: 2026-01-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-multilang-translation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

開發一個內網多國語言翻譯系統，供員工快速進行文字翻譯。系統採用 Python 3.11+ / Django 4.2+ (ASGI) 單體架構，前端使用 Django Templates + HTMX + Alpine.js，模型推論直接整合於應用程式內。支援 8 種語言互譯、自動語言偵測、翻譯品質設定、歷史記錄等功能，並提供系統狀態監控頁面供管理人員使用。

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Django 4.2+ (ASGI), transformers, HTMX, Alpine.js, torch  
**Storage**: Django Cache Framework (記憶體快取)、sessionStorage (前端設定/歷史)、無傳統資料庫  
**Testing**: pytest, pytest-django, pytest-asyncio  
**Target Platform**: Windows/Linux 內網伺服器  
**Project Type**: web (Django 單體應用)  
**Performance Goals**: GPU 模式 2-3 秒/千字、CPU 模式 8-10 秒/千字 (95th percentile)、100 並發使用者  
**Constraints**: 完全離線運作、翻譯逾時 120 秒、最大 10,000 字元、記憶體內資料不持久化  
**Scale/Scope**: 100 並發使用者、200 最大佇列請求、24 小時統計視窗

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Offline-First Architecture ✅ 通過
- ✅ TAIDE-LX-7B 模型本地部署，無外部 API 呼叫
- ✅ 所有依賴套件可離線安裝（pip wheel）
- ✅ 無 CDN 或雲端服務依賴（HTMX/Alpine.js 靜態檔案本地託管）

### II. Performance as a Feature ✅ 通過
- ✅ GPU 模式目標：2-3 秒/千字（符合 constitution 要求）
- ✅ CPU 模式目標：8-10 秒/千字（符合 constitution 要求）
- ✅ 100 並發使用者支援（符合 constitution 要求）

### III. Simplicity and Pragmatism ✅ 完全符合
- ✅ Django 4.2+ 符合 constitution 指定技術棧
- ✅ Django Templates + HTMX + Alpine.js 符合「避免重型 SPA 框架」原則
- ✅ 單體架構，無不必要的微服務拆分
- ✅ 使用 Django 內建功能（Cache Framework、Templates）

### IV. Test-Driven Development ✅ 待執行
- 📋 需建立：tests/unit/ (pytest)
- 📋 需建立：tests/integration/ (API 契約測試)
- 📋 需建立：tests/performance/ (負載測試)

### V. Observability and Maintainability ✅ 通過
- ✅ FR-040/FR-041/FR-042 定義日誌記錄需求
- ✅ FR-035/FR-036 定義監控指標
- ✅ FR-045 定義健康檢查端點

### VI. Configuration Over Code ✅ 通過
- ✅ YAML 配置檔案：config/app_config.yaml, config/model_config.yaml, config/languages.yaml
- ✅ IP 白名單透過設定檔配置
- ✅ 逾時閾值、日誌保留期限可配置

### VII. API-First Design ✅ 待執行
- 📋 需定義 REST API 契約（contracts/）
- 📋 需定義錯誤碼標準

### 閘門狀態：✅ 通過
- 所有核心原則完全符合 Constitution 要求
- 技術棧選擇與 Constitution 一致（Django 4.2+）
- 可進入 Phase 0 研究階段

## Project Structure

### Documentation (this feature)

```text
specs/001-multilang-translation/
├── plan.md              # 本檔案（/speckit.plan 輸出）
├── research.md          # Phase 0 輸出 - 技術研究
├── data-model.md        # Phase 1 輸出 - 資料模型
├── quickstart.md        # Phase 1 輸出 - 快速入門
├── contracts/           # Phase 1 輸出 - API 契約
│   ├── api-contract.md  # API 契約說明
│   └── openapi.yaml     # OpenAPI 規格
└── tasks.md             # Phase 2 輸出（/speckit.tasks 產出，尚未建立）
```

### Source Code (repository root)

```text
# Django 單體應用架構

translation_project/              # Django 專案根目錄
├── manage.py
├── translation_project/          # Django 專案設定
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                   # ASGI 入口（支援非同步）
│   └── wsgi.py
│
├── translator/                   # Django 應用程式
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                 # Django 模型（僅用於定義資料結構）
│   ├── views.py                  # 視圖（頁面渲染）
│   ├── api/                      # REST API
│   │   ├── __init__.py
│   │   ├── views.py              # API 視圖
│   │   ├── serializers.py        # 序列化器
│   │   └── urls.py               # API 路由
│   ├── services/                 # 商業邏輯服務
│   │   ├── __init__.py
│   │   ├── translation_service.py
│   │   ├── queue_service.py
│   │   ├── statistics_service.py
│   │   └── model_service.py      # TAIDE-LX-7B 模型載入與推論
│   ├── middleware/               # 中介軟體
│   │   ├── __init__.py
│   │   └── ip_whitelist.py
│   ├── templates/                # Django Templates
│   │   └── translator/
│   │       ├── base.html
│   │       ├── index.html        # 主翻譯頁面
│   │       ├── settings.html     # 設定頁面
│   │       └── admin_status.html # 系統狀態頁面
│   └── static/                   # 靜態檔案
│       └── translator/
│           ├── css/
│           ├── js/
│           │   ├── htmx.min.js   # HTMX（本地託管）
│           │   └── alpine.min.js # Alpine.js（本地託管）
│           └── img/
│
├── config/                       # 配置檔案
│   ├── app_config.yaml
│   ├── model_config.yaml
│   └── languages.yaml
│
├── logs/                         # 日誌目錄（執行時產生）
│
└── models/                       # TAIDE-LX-7B 模型檔案（現有）
    └── models--taide--TAIDE-LX-7B/

tests/
├── unit/                         # 單元測試
├── integration/                  # 整合測試
└── performance/                  # 效能測試
```

**Structure Decision**: 採用 Django 單體應用架構，符合 Constitution 的「Simplicity and Pragmatism」原則。模型推論直接整合於 Django 應用內，無需額外微服務，簡化部署與維護。

## Complexity Tracking

> **無 Constitution 違規項目**

本設計完全符合 Constitution 要求，無需記錄複雜度偏差。

---

## Phase 完成狀態

- [x] Phase 0: 研究 (research.md)
- [x] Phase 1: 設計 (data-model.md, contracts/, quickstart.md)
- [ ] Phase 2: 任務分解 (tasks.md - 由 /speckit.tasks 產出)
