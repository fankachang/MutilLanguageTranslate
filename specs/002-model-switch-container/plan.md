# Implementation Plan: 模型切換、狀態頁公開、容器化啟動

**Branch**: `002-model-switch-container` | **Date**: 2026年1月21日 | **Spec**: [specs/002-model-switch-container/spec.md](specs/002-model-switch-container/spec.md)
**Input**: Feature specification from `/specs/002-model-switch-container/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

- 翻譯頁新增「可用模型清單」並支援模型切換；切換期間要顯示載入狀態並禁止送出翻譯。
- 狀態頁與其所需的狀態資料改為匿名可存取（不需管理者/不需 IP 白名單）。
- 維持現有 Podman/Docker/Compose 容器化啟動能力，並以 `/api/health/` 做健康檢查。

Phase 0/1 產物：
- Phase 0：
  - [specs/002-model-switch-container/research.md](specs/002-model-switch-container/research.md)
- Phase 1：
  - [specs/002-model-switch-container/data-model.md](specs/002-model-switch-container/data-model.md)
  - [specs/002-model-switch-container/contracts/openapi.yaml](specs/002-model-switch-container/contracts/openapi.yaml)
  - [specs/002-model-switch-container/quickstart.md](specs/002-model-switch-container/quickstart.md)

## Technical Context

**Language/Version**: Python 3.11（Containerfile）
**Primary Dependencies**: Django 4.2+、uvicorn（ASGI）、transformers/torch/accelerate（本地推論）、PyYAML（設定）、psutil（監控）
**Storage**: SQLite（Django 預設），快取（LocMemCache）用於佇列/統計；模型檔案以檔案系統（`models/`）存放
**Testing**: pytest、pytest-django（既有 `tests/`）
**Target Platform**: 內網 Linux 容器環境（Docker/Podman），本機開發可在 Windows 進行
**Project Type**: Django Web application（Server-rendered templates + REST API）
**Performance Goals**: 依憲法：GPU 1000 字元翻譯 p95 2-3s；CPU p95 8-10s；並發 100 使用者為目標值（未經 perf test 驗證前，不宣稱達標）
**Constraints**: Offline-first（不可依賴外網/CDN）；避免過度設計；API/路由穩定；新增設定走 YAML
**Scale/Scope**: 單機部署；多模型（多個本地模型目錄）可切換；狀態頁需可被匿名使用者讀取

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Offline-first: No external network dependencies (no CDN/cloud calls)
- Performance: Define targets + include a validation approach (perf test when claiming concurrency)
- Simplicity: Avoid over-engineering; justify any added complexity in "Complexity Tracking"
- TDD: Define test strategy; write failing tests before implementation changes
- Observability: Logging/health/status visibility included for operability
- Config-over-code: New limits/paths/timeouts are configurable (YAML), not hardcoded
- API-first & stability: Public interfaces are contracts; avoid breaking changes
- Identifier stability: Do not rename existing identifiers unless required; update all call sites
- No-hallucination integration: Frontend must only call backend endpoints/functions that exist

本計畫預期採取的合規策略：
- Offline-first：模型清單來源為本機 `models/` 子目錄掃描，不引入外部 API；容器映像不依賴 CDN。
- TDD：新增模型清單/選擇 API、狀態頁匿名可用、容器啟動指令等變更前，先補齊對應單元/整合測試。
- API-first：新增 `/api/v1/models/*`、`/api/v1/status/*` 採明確 JSON schema；保留既有端點避免破壞相容性。
- Identifier stability：不任意更名既有 `translate`、`/api/health/`、`/api/v1/translate/` 等端點；新增端點以擴充方式提供。

Phase 1 設計完成後 re-check：PASS（未新增外部依賴、未引入非必要複雜度；所有變更以新增端點/欄位維持向後相容）。

## Project Structure

### Documentation (this feature)

```text
specs/002-model-switch-container/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
translation_project/
├── manage.py
├── translation_project/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
└── translator/
    ├── api/
    │   ├── urls.py
    │   └── views.py
    ├── middleware/
    │   └── ip_whitelist.py
    ├── services/
    │   ├── model_service.py
    │   └── model_providers/
    ├── templates/
    │   └── translator/
    ├── urls.py
    └── views.py

config/
├── app_config.yaml
├── model_config.yaml
└── languages.yaml

models/
└── <model-name>/

tests/
├── unit/
├── integration/
└── performance/
```

**Structure Decision**: 既有 Django 專案結構不更動；本次功能以新增/擴充 `translator` app 的 API、服務層與模板為主。

## Complexity Tracking

本功能無需新增額外複雜度；Constitution Check 無違規。
