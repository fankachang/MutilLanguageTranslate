---
description: "Task list for feature implementation"
---

# Tasks: 模型切換、狀態頁公開、容器化啟動

**Input**: 設計文件位於 `specs/002-model-switch-container/`
- `plan.md`
- `spec.md`
- `research.md`
- `data-model.md`
- `contracts/openapi.yaml`
- `quickstart.md`

**Tests**: 依專案憲法，本功能採 TDD；每個 User Story 必須具備可獨立驗證的測試任務。

## Phase 1: Setup（共用基礎設定）

- [x] T001 建立 pytest 設定於 pytest.ini（設定 `DJANGO_SETTINGS_MODULE=translation_project.settings`）
- [x] T002 [P] 新增 tests/conftest.py（提供 Django client、tmp models 目錄、override settings 等共用 fixture）
- [x] T003 [P] 補齊 tests/unit/__init__.py 與 tests/integration/__init__.py（若缺）
- [x] T004 [P] 建立測試用輔助工具 tests/helpers/model_fixtures.py（快速建立 `models/<id>/config.json` 目錄結構）

---

## Phase 2: Foundational（阻塞性前置，所有 US 共用）

- [x] T005 新增模型識別驗證工具於 translation_project/translator/utils/model_id.py（拒絕 `..`、路徑分隔符、絕對路徑）
- [x] T006 擴充錯誤碼於 translation_project/translator/errors.py（新增：`MODEL_NOT_FOUND`、`MODEL_INVALID_ID`、`MODEL_SWITCH_IN_PROGRESS`、`MODEL_SWITCH_REJECTED`、`MODEL_SWITCH_FAILED`）
- [x] T007 [P] 更新 config/model_config.yaml.example（新增模型掃描/預設模型/切換政策設定鍵；保留向後相容預設）
- [x] T008 [P] 新增模型目錄掃描服務於 translation_project/translator/services/model_catalog_service.py（輸出 ModelEntry 清單）

**Checkpoint**: Foundation ready（T001-T008 完成後，US1/US2/US3 可並行開工）

---

## Phase 3: User Story 1（Priority: P1）— 模型清單與切換翻譯 🎯 MVP

**Goal**: 翻譯頁顯示可用模型清單，使用者可切換模型並以選定模型完成翻譯；切換期間 UI 需顯示載入中並禁止送出。

**Independent Test**: 啟動服務 → 開啟 `/` → 看到模型清單（資料夾名）→ 切到模型 B → 發送翻譯（帶 `model_id=B`）→ 服務端接收並回應成功；切換中不可送出。

### Tests（先寫先失敗）

- [x] T009 [P] [US1] 單元測試：模型掃描規則於 tests/unit/test_model_catalog_service.py
- [x] T010 [P] [US1] 整合測試：模型清單/選擇/切換 API 於 tests/integration/test_models_endpoints.py
- [x] T011 [P] [US1] 整合測試：翻譯 API 支援 `model_id`（不觸發真實大模型載入，使用 monkeypatch/mock）於 tests/integration/test_translate_with_model_id.py
- [x] T012 [P] [US1] 單元測試：翻譯頁模板包含模型選擇 UI 與切換中禁用邏輯（以字串/片段驗證）於 tests/unit/test_translation_page_model_ui.py

### Implementation

- [x] T013 [US1] 擴充 ModelService 支援 active model id 與切換（兩階段提交、失敗回退、鎖避免並發切換）於 translation_project/translator/services/model_service.py
- [x] T014 [US1] 調整 LocalModelProvider 支援以 `provider.local.path` 指向任意 `models/<model_id>`（避免硬編碼 snapshot 路徑）於 translation_project/translator/services/model_providers/local_provider.py
- [x] T015 [US1] 新增模型相關 API：`GET /api/v1/models/`、`PUT /api/v1/models/selection/`、`POST /api/v1/models/switch/` 於 translation_project/translator/api/views.py
- [x] T016 [US1] 註冊模型相關路由於 translation_project/translator/api/urls.py
- [x] T017 [US1] 翻譯頁新增模型選擇元件與切換狀態（含：載入中提示、禁用翻譯按鈕、sessionStorage 保存選擇、翻譯 request 帶 `model_id`）於 translation_project/translator/templates/translator/index.html
- [x] T018 [US1] 翻譯 API 解析 `model_id`（可選）並在必要時觸發切換/或依政策回應錯誤（維持既有行為向後相容）於 translation_project/translator/api/views.py

**Checkpoint**: US1 可獨立 Demo（模型清單顯示/切換/翻譯流程全通，且測試全綠）

---

## Phase 4: User Story 2（Priority: P2）— 狀態頁公開（匿名可用）

**Goal**: 未登入使用者可直接開啟狀態頁，且狀態頁相依的狀態資料 API 不回 401/403。

**Independent Test**: 以匿名瀏覽器訪問 `/admin/status/` 回 200；頁面抓取狀態資料時改打 public API 並回 200。

### Tests（先寫先失敗）

- [x] T019 [P] [US2] 整合測試：匿名 GET `/admin/status/` 回 200 於 tests/integration/test_status_page_public.py
- [x] T020 [P] [US2] 整合測試：匿名 GET `/api/v1/status/`、`/api/v1/statistics/`、`/api/v1/model/load-progress/` 回 200 於 tests/integration/test_public_status_endpoints.py
- [x] T021 [P] [US2] 單元測試：狀態頁模板 fetch URL 已改為 public endpoints（避免打 `/api/v1/admin/*`）於 tests/unit/test_status_page_fetch_urls.py

### Implementation

- [x] T022 [US2] 新增 public 只讀狀態 API（沿用既有 admin schema）於 translation_project/translator/api/views.py
- [x] T023 [US2] 註冊 public 狀態 API 路由於 translation_project/translator/api/urls.py
- [x] T024 [US2] 狀態頁模板改抓 public endpoints（保留具副作用的 admin 操作仍走 `/api/v1/admin/*`）於 translation_project/translator/templates/translator/admin_status.html

**Checkpoint**: US2 可獨立 Demo（匿名狀態頁可開啟且可讀取狀態資料）

---

## Phase 5: User Story 3（Priority: P3）— 容器建置與啟動（Podman/Docker/Compose）

**Goal**: 可用 Podman/Docker 建置並啟動；Compose 一鍵啟動；健康檢查 `/api/health/` 可用。

**Independent Test**: `podman build` 或 `docker build` 成功；`docker compose up -d` 後 `GET /api/health/` 回 200。

### Tests（先寫先失敗）

- [x] T025 [P] [US3] 單元測試：Containerfile 不應硬依賴未安裝的 uvloop（避免啟動即失敗）於 tests/unit/test_containerfile_runtime.py
- [x] T026 [P] [US3] 單元測試：docker-compose.yaml 具備必要 ports/volumes/healthcheck 設定於 tests/unit/test_docker_compose_config.py
- [x] T027 [P] [US3] 整合測試：`GET /api/health/` 回 200（不依賴容器）於 tests/integration/test_health_endpoint.py

### Implementation

- [x] T028 [US3] 修正 Containerfile 啟動參數（移除 `--loop uvloop` 或補齊 uvloop 依賴，二擇一並以測試鎖定）於 Containerfile
- [x] T029 [US3] 確認 docker-compose.yaml 具備 models/config/logs 掛載與 healthcheck（必要時修正）於 docker-compose.yaml
- [x] T030 [US3] 補齊容器驗證步驟文件（與現有 quickstart.md 一致）於 specs/002-model-switch-container/quickstart.md

**Checkpoint**: US3 可獨立驗收（容器 build/run/compose + healthcheck）

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T031 [P] 更新 README 的容器章節（移除「Compose 未完成」等過時描述，保持與 docker-compose.yaml 一致）於 README.md
- [x] T032 統一前端錯誤訊息呈現（模型切換/無可用模型/切換失敗）於 translation_project/translator/templates/translator/index.html
- [x] T033 以 quickstart.md 的步驟做一次端到端驗證並修正文件差異；同時記錄並回填 SC-001~SC-004 的驗收量測結果與環境條件（若時間門檻不穩定，至少需能重現量測方式）於 specs/002-model-switch-container/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1（Setup）→ Phase 2（Foundational）→ Phase 3/4/5（US1/US2/US3 可並行）→ Phase 6（Polish）

### User Story Dependencies

- US1（P1）：僅依賴 Phase 1-2
- US2（P2）：僅依賴 Phase 1-2（不依賴 US1/US3）
- US3（P3）：僅依賴 Phase 1-2（不依賴 US1/US2）

### Parallel Opportunities

- Phase 1：T002-T004 可並行
- Phase 2：T007-T008 可並行
- US1：T009-T012 可並行（不同檔案），Implementation 中 T015/T016 可並行
- US2：T019-T021 可並行；Implementation 中 T022/T023 可並行
- US3：T025-T027 可並行；Implementation 中 T028/T029 可並行

---

## Parallel Example（每個 US）

### US1

可並行：T009、T010、T011、T012（不同測試檔案）；以及實作階段的 T015 與 T016（views/urls）。

### US2

可並行：T019、T020、T021（不同測試檔案）；以及實作階段的 T022 與 T023（views/urls）。

### US3

可並行：T025、T026、T027（不同測試檔案）；以及實作階段的 T028 與 T029（Containerfile/compose）。

---

## Implementation Strategy

- MVP 建議範圍：先完成 US1（Phase 3），可立即驗收「可用模型清單 + 切換 + 翻譯」。
- 每個 US 皆遵循：先測試（Fail）→ 最小實作（Pass）→ 文件/整合驗證。
