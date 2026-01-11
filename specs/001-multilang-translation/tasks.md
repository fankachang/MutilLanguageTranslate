# Tasks: 多國語言翻譯系統

**Input**: Design documents from `/specs/001-multilang-translation/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: 本專案未明確要求 TDD，故測試任務為可選項，將在 Polish 階段處理。

**Organization**: 任務按 User Story 組織，以便每個故事可獨立實作與測試。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可平行執行（不同檔案、無相依性）
- **[Story]**: 所屬 User Story（如 US1, US2, US3）
- 描述中包含精確檔案路徑

## Path Conventions

依 plan.md 定義的專案結構：
- **Django 專案**: `translation_project/`
- **Django 應用**: `translation_project/translator/`
- **配置檔**: `config/`
- **測試**: `tests/`

---

## Phase 1: Setup（專案初始化）

**Purpose**: 建立專案基礎結構與開發環境

- [X] T001 建立 Django 專案結構 `translation_project/` 與應用程式 `translator/`
- [X] T002 [P] 建立 requirements.txt 依賴清單（Django 4.2+, uvicorn, transformers, torch, PyYAML, psutil）
- [X] T003 [P] 建立配置目錄 `config/` 與範本檔案（app_config.yaml.example, model_config.yaml.example, languages.yaml）
- [X] T004 [P] 建立日誌目錄 `logs/.gitkeep` 與測試目錄結構 `tests/unit/`, `tests/integration/`, `tests/performance/`
- [X] T005 [P] 設定 Django settings.py（ASGI、Cache Framework、靜態檔案、日誌配置）
- [X] T006 [P] 下載並設定 HTMX、Alpine.js 靜態檔案至 `translator/static/translator/js/`

---

## Phase 2: Foundational（基礎建設）

**Purpose**: 所有 User Story 共用的核心基礎設施

**⚠️ CRITICAL**: 此階段必須完成後，才能開始任何 User Story 的開發

- [X] T007 建立資料類別定義 `translator/models.py`（Language, TranslationRequest, TranslationResponse, QueueItem, SystemStatus, TranslationStatistics）
- [X] T008 [P] 建立列舉值定義 `translator/enums.py`（QualityMode, TranslationStatus, QueueStatus, ExecutionMode, ModelStatus）
- [X] T009 [P] 建立錯誤代碼定義 `translator/errors.py`（錯誤代碼常數、錯誤訊息對照表）
- [X] T010 實作 TAIDE-LX-7B 模型服務 `translator/services/model_service.py`（單例載入、GPU/CPU 自動偵測、生成參數配置、載入失敗錯誤處理）
- [X] T011 實作佇列服務 `translator/services/queue_service.py`（threading.Lock、並發控制、等待佇列管理）
- [X] T012 [P] 實作統計服務 `translator/services/statistics_service.py`（滑動視窗、分鐘快照、24 小時統計）
- [X] T013 [P] 實作 IP 白名單中介軟體 `translator/middleware/ip_whitelist.py`（CIDR 解析、內網/管理員 IP 驗證）
- [X] T014 設定 Django URL 路由 `translation_project/urls.py` 與 `translator/api/urls.py`
- [X] T015 建立基礎模板 `translator/templates/translator/base.html`（HTML 骨架、HTMX/Alpine.js 載入、主題切換）
- [X] T016 [P] 建立配置載入工具 `translator/utils/config_loader.py`（YAML 解析、驗證）

**Checkpoint**: 基礎設施就緒 - 可開始 User Story 平行開發

---

## Phase 3: User Story 1 - 基本文字翻譯 (Priority: P1) 🎯 MVP

**Goal**: 員工可輸入原文、選擇目標語言、執行翻譯並複製結果

**Independent Test**: 輸入「你好世界」並選擇英文作為目標語言，期望獲得英文翻譯結果並可複製

### Implementation for User Story 1

- [ ] T017 [US1] 實作翻譯服務核心 `translator/services/translation_service.py`（Prompt 組裝、模型呼叫、結果解析、FR-006 換行格式保留、FR-038 Prompt 注入防護）
- [ ] T018 [US1] 實作翻譯 API 視圖 `translator/api/views.py` - POST /api/v1/translate/（請求驗證、佇列處理、回應格式化）
- [ ] T018b [US1] 實作狀態查詢 API 視圖 `translator/api/views.py` - GET /api/v1/translate/{request_id}/status/（佇列位置、處理狀態）
- [ ] T019 [US1] 實作翻譯 API 序列化器 `translator/api/serializers.py`（TranslationRequestSerializer, TranslationResponseSerializer）
- [ ] T020 [US1] 建立主翻譯頁面模板 `translator/templates/translator/index.html`（HTMX 表單、Alpine.js 狀態管理）
- [ ] T021 [US1] 實作頁面視圖 `translator/views.py` - 首頁渲染（語言列表注入）
- [ ] T022 [US1] 建立翻譯結果片段模板 `translator/templates/translator/partials/result.html`（HTMX 回應片段）
- [ ] T023 [US1] 實作前端字數統計與複製功能 `translator/static/translator/js/translation.js`（FR-005 即時字數統計、剪貼簿 API）
- [ ] T024 [US1] 建立翻譯頁面樣式 `translator/static/translator/css/main.css`（響應式佈局、載入動畫）

**Checkpoint**: User Story 1 完成 - 基本翻譯功能可獨立運作與測試

---

## Phase 4: User Story 2 - 多語言選擇與自動偵測 (Priority: P1)

**Goal**: 員工可選擇 8 種語言、使用自動偵測、快速交換語言

**Independent Test**: 輸入日文文字並選擇「自動偵測」為來源語言、韓文為目標語言，期望系統正確識別並完成翻譯

### Implementation for User Story 2

- [ ] T025 [US2] 實作語言 API 視圖 `translator/api/views.py` - GET /api/v1/languages/（語言清單）
- [ ] T026 [US2] 擴展翻譯服務 `translator/services/translation_service.py`（自動語言偵測、信心分數解析、回退邏輯）
- [ ] T027 [US2] 更新翻譯頁面模板 `translator/templates/translator/index.html`（語言下拉選單、自動偵測選項、語言交換按鈕）
- [ ] T028 [US2] 實作語言交換功能 `translator/static/translator/js/translation.js`（Alpine.js 雙向綁定）
- [ ] T029 [US2] 建立偵測語言顯示片段 `translator/templates/translator/partials/detected_lang.html`

**Checkpoint**: User Story 2 完成 - 多語言功能可獨立運作與測試

---

## Phase 5: User Story 3 - 錯誤處理與使用者提示 (Priority: P1)

**Goal**: 系統在發生錯誤時提供清晰的中文錯誤訊息

**Independent Test**: 輸入空白文字、超過字數限制的文字，或模擬網路中斷來測試各種錯誤提示

### Implementation for User Story 3

- [ ] T030 [US3] 實作前端驗證 `translator/static/translator/js/validation.js`（空白檢查、字數限制、相同語言檢查）
- [ ] T031 [US3] 建立錯誤訊息片段模板 `translator/templates/translator/partials/error.html`（錯誤代碼對應中文訊息）
- [ ] T032 [US3] 更新 API 視圖錯誤處理 `translator/api/views.py`（ValidationError、ServiceUnavailable、Timeout 處理）
- [ ] T033 [US3] 實作 API 例外處理器 `translator/api/exception_handlers.py`（統一錯誤回應格式）
- [ ] T034 [US3] 建立錯誤訊息樣式 `translator/static/translator/css/error.css`（警告/錯誤樣式）

**Checkpoint**: User Story 3 完成 - 錯誤處理功能可獨立運作與測試

---

## Phase 6: User Story 4 - 使用者設定調整 (Priority: P2)

**Goal**: 員工可調整翻譯品質、介面主題、字體大小

**Independent Test**: 調整主題為暗色、字體為大，重新整理頁面後檢查設定是否保留（同一標籤頁）

### Implementation for User Story 4

- [ ] T035 [US4] 建立設定頁面模板 `translator/templates/translator/settings.html`（品質選擇、主題切換、字體大小）
- [ ] T036 [US4] 實作設定頁面視圖 `translator/views.py` - 設定頁面渲染
- [ ] T037 [US4] 實作 sessionStorage 設定管理 `translator/static/translator/js/settings.js`（儲存、讀取、套用設定）
- [ ] T038 [US4] 建立主題樣式 `translator/static/translator/css/themes.css`（亮色/暗色主題 CSS 變數）
- [ ] T039 [US4] 更新基礎模板 `translator/templates/translator/base.html`（套用使用者設定）

**Checkpoint**: User Story 4 完成 - 設定功能可獨立運作與測試

---

## Phase 7: User Story 5 - 翻譯歷史記錄 (Priority: P2)

**Goal**: 系統記錄當前會話的最近 20 筆翻譯記錄

**Independent Test**: 執行多次翻譯後，檢查歷史記錄列表是否正確顯示，並點擊記錄驗證是否可重現

### Implementation for User Story 5

- [ ] T040 [US5] 實作歷史記錄管理 `translator/static/translator/js/history.js`（sessionStorage 儲存、20 筆上限、FIFO）
- [ ] T041 [US5] 建立歷史記錄列表片段 `translator/templates/translator/partials/history_list.html`
- [ ] T042 [US5] 更新翻譯頁面模板 `translator/templates/translator/index.html`（歷史記錄側邊欄/折疊區）
- [ ] T043 [US5] 實作歷史記錄點擊重現功能 `translator/static/translator/js/history.js`（填入原文/譯文/語言設定）

**Checkpoint**: User Story 5 完成 - 歷史記錄功能可獨立運作與測試

---

## Phase 8: User Story 6 - 系統狀態監控 (Priority: P2)

**Goal**: 管理人員可查看系統狀態、資源使用、翻譯統計

**Independent Test**: 訪問系統狀態頁面，檢查是否顯示系統狀態、並發請求數、記憶體、CPU 使用率等資訊

### Implementation for User Story 6

- [ ] T044 [US6] 實作系統狀態 API 視圖 `translator/api/views.py` - GET /api/v1/admin/status/（系統狀態、資源使用）
- [ ] T045 [US6] 實作統計 API 視圖 `translator/api/views.py` - GET /api/v1/admin/statistics/（24 小時統計）
- [ ] T046 [US6] 建立系統狀態頁面模板 `translator/templates/translator/admin_status.html`
- [ ] T047 [US6] 實作系統狀態頁面視圖 `translator/views.py` - 管理頁面渲染（IP 白名單驗證）
- [ ] T048 [US6] 建立狀態頁面樣式 `translator/static/translator/css/admin.css`（儀表板佈局、指標卡片）
- [ ] T049 [US6] 實作系統資源監控 `translator/services/monitor_service.py`（psutil CPU/記憶體、GPU VRAM）

**Checkpoint**: User Story 6 完成 - 系統監控功能可獨立運作與測試

---

## Phase 9: 健康檢查與維運 (Cross-Cutting)

**Purpose**: 系統維運相關功能

- [ ] T050 實作健康檢查 API `translator/api/views.py` - GET /api/health/（API 回應、模型狀態驗證）
- [ ] T051 實作優雅停止機制 `translator/services/shutdown_service.py`（SIGTERM 處理、等待進行中請求、120 秒超時）
- [ ] T052 實作日誌輪替配置 `translation_project/settings.py`（RotatingFileHandler、30 天保留）
- [ ] T053 [P] 建立日誌記錄工具 `translator/utils/logger.py`（翻譯請求日誌、錯誤日誌）

---

## Phase 10: Polish & 驗收準備

**Purpose**: 最終調整與驗收

- [ ] T054 [P] 建立 Containerfile（Podman 部署配置）
- [ ] T055 [P] 更新 README.md（專案說明、快速開始）
- [ ] T056 程式碼清理與重構（移除 debug 程式碼、統一程式碼風格）
- [ ] T057 執行 quickstart.md 驗證（依照文件步驟測試部署流程）
- [ ] T058 [P] 建立單元測試 `tests/unit/`（Constitution IV 要求，建議 MVP 後補充）
- [ ] T059 [P] 建立整合測試 `tests/integration/`（Constitution IV 要求，建議 MVP 後補充）
- [ ] T060 [P] 建立效能測試 `tests/performance/`（驗證 100 並發目標，建議上線前完成）

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)           → 無相依性，可立即開始
    ↓
Phase 2 (Foundational)    → 依賴 Phase 1，阻擋所有 User Stories
    ↓
Phase 3-8 (User Stories)  → 依賴 Phase 2，可平行執行
    ↓
Phase 9 (維運)            → 依賴 Phase 2，可與 User Stories 平行
    ↓
Phase 10 (Polish)         → 依賴所有想完成的功能
```

### User Story Dependencies

| Story | Priority | 可開始條件 | 與其他 Story 的關係 |
|-------|----------|-----------|-------------------|
| US1 基本翻譯 | P1 | Phase 2 完成 | 獨立，為其他 Story 基礎 |
| US2 多語言 | P1 | Phase 2 完成 | 擴展 US1 的翻譯功能 |
| US3 錯誤處理 | P1 | Phase 2 完成 | 橫跨所有功能 |
| US4 使用者設定 | P2 | Phase 2 完成 | 獨立 |
| US5 歷史記錄 | P2 | Phase 2 完成 | 需要 US1 翻譯結果 |
| US6 系統監控 | P2 | Phase 2 完成 | 獨立 |

### Parallel Opportunities

**Phase 1 內可平行**:
- T002, T003, T004, T005, T006

**Phase 2 內可平行**:
- T008, T009 可與 T007 平行
- T012, T013 可與 T010, T011 平行
- T016 可與其他任務平行

**User Stories 間可平行**:
- US1, US2, US3 為 P1，建議依序完成作為 MVP
- US4, US5, US6 為 P2，可平行開發

---

## Implementation Strategy

### MVP 範圍（建議）

**最小可行產品 = Phase 1 + Phase 2 + US1 + US2 + US3**

完成 MVP 後系統可：
- 執行基本文字翻譯
- 支援 8 種語言與自動偵測
- 提供完整錯誤處理

### Incremental Delivery

1. **Sprint 1**: Setup + Foundational（T001-T016）
2. **Sprint 2**: US1 基本翻譯 + US2 多語言（T017-T029）
3. **Sprint 3**: US3 錯誤處理 + US4 設定（T030-T039）
4. **Sprint 4**: US5 歷史 + US6 監控（T040-T049）
5. **Sprint 5**: 維運 + Polish（T050-T060）

---

## Summary

| 項目 | 數量 |
|------|------|
| 總任務數 | 61 |
| Setup 任務 | 6 |
| Foundational 任務 | 10 |
| US1 任務 | 9 |
| US2 任務 | 5 |
| US3 任務 | 5 |
| US4 任務 | 5 |
| US5 任務 | 4 |
| US6 任務 | 6 |
| 維運任務 | 4 |
| Polish 任務 | 7 |
| 可平行任務 | 23 |

**MVP 範圍**: Phase 1-2 + US1-US3 = 35 任務
