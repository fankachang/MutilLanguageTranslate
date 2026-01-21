# Feature Specification: 模型切換、狀態頁公開、容器化啟動

**Feature Branch**: `002-model-switch-container`
**Created**: 2026年1月21日
**Status**: Draft
**Input**: 需求來源：[Prompt/request2.md](../../Prompt/request2.md)

## User Scenarios & Testing *(mandatory)*

**Constitution note**: This project requires TDD. Each user story MUST be independently testable and have explicit acceptance scenarios.

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - [Brief Title] (Priority: P1)

使用者可在翻譯頁面看到「可用模型清單」，並可切換模型後使用選定模型完成翻譯。

**Why this priority**: 這是本次擴充的核心價值（支援新增模型並讓使用者可選），不具備此能力即無法驗收本功能。

**Independent Test**: 可在不依賴狀態頁與容器啟動需求的情況下，僅以「啟動→開啟翻譯頁→切換模型→送出翻譯」驗證結果。

**Acceptance Scenarios**:

1. **Given** 系統啟動後於模型目錄中偵測到 `Translategemma-4b-it` 與 `Translategemma-12b-it`，**When** 使用者開啟翻譯頁面，**Then** 模型選擇元件顯示上述兩個選項，且顯示名稱與模型目錄名稱完全一致。
2. **Given** 模型清單至少包含模型 A 與模型 B，**When** 使用者選擇模型 B 並執行一次翻譯，**Then** 該次翻譯結果由模型 B 產生。
3. **Given** 使用者正在切換模型且切換尚未完成，**When** 使用者嘗試送出翻譯，**Then** 翻譯操作被阻止（例如按鈕不可用）且介面顯示「載入/切換中」狀態。
4. **Given** 模型目錄不存在任何可用模型，**When** 使用者開啟翻譯頁面，**Then** 介面顯示明確提示（例如未偵測到可用模型）且翻譯操作不可用。

---

### User Story 2 - [Brief Title] (Priority: P2)

任何使用者（不需登入、不需管理者權限）都能查看系統狀態頁面。

**Why this priority**: 需求明確要求移除管理者限制，避免在導入或展示時產生阻礙。

**Independent Test**: 可在不操作翻譯功能、也不切換模型的前提下，直接以瀏覽器匿名訪問狀態頁驗證。

**Acceptance Scenarios**:

1. **Given** 使用者未登入且無任何權限資訊，**When** 訪問系統狀態頁面，**Then** 頁面可正常顯示且不要求管理者權限。
2. **Given** 使用者未登入且無任何權限資訊，**When** 狀態頁載入其所需的狀態資料（若有），**Then** 資料可正常取得且不要求管理者權限。

---

### User Story 3 - [Brief Title] (Priority: P3)

維運/部署者可以用 Podman 或 Docker（含 Compose）建置映像並啟動服務，透過健康檢查確認服務可用。

**Why this priority**: 需求明確要求可直接以容器工具啟動服務，降低部署門檻並提升可重現性。

**Independent Test**: 不需驗證 UI 細節；僅需建置映像、以預設連接埠啟動、並確認健康檢查可達。

**Acceptance Scenarios**:

1. **Given** 專案根目錄提供容器建置檔，**When** 以 Podman 或 Docker 進行映像建置，**Then** 建置流程完成且產出可執行映像。
2. **Given** 主機端已準備模型目錄並以唯讀方式掛載至容器內的既定模型路徑，**When** 以預設對外連接埠啟動容器，**Then** 使用者可透過瀏覽器/HTTP 存取服務首頁或翻譯頁。
3. **Given** 服務啟動完成，**When** 使用者以系統提供的健康檢查網址發送請求，**Then** 回應顯示服務健康。
4. **Given** 專案提供 Compose 啟動設定，**When** 以 Compose 一鍵啟動服務，**Then** 健康檢查可用且服務對外可連線。

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- 模型目錄下存在子目錄，但缺少必要的模型設定檔/資源時，不得列為可用模型。
- 模型顯示在清單中，但使用者切換時載入失敗時：需顯示可理解的錯誤訊息，且系統可回退到先前可用模型。
- 在模型切換進行中再次切換：介面應避免造成無回應或狀態混亂（例如佇列/取消前一次切換）。
- 未登入使用者同時大量訪問狀態頁：頁面仍需可讀取，不應因權限判定而失敗。
- 容器啟動但未掛載模型目錄：系統需以明確方式呈現「無可用模型」狀態，而非崩潰。

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: 系統 MUST 在啟動時掃描模型目錄下的子目錄並產出「可用模型清單」。
- **FR-002**: 系統 MUST 以「目錄存在且可讀取」且「包含必要的模型設定檔/資源」作為可用模型的最低判定條件。
- **FR-003**: 翻譯頁面 MUST 提供模型選擇元件，並以模型目錄名稱作為顯示名稱（不得自行改名或硬編碼別名）。
- **FR-004**: 使用者 MUST 能切換模型，且切換成功後的翻譯請求 MUST 使用被選定的模型產生結果。
- **FR-005**: 當模型切換尚未完成時，系統 MUST 對使用者呈現「載入/切換中」狀態，並避免使用者送出會導致錯誤的翻譯操作。
- **FR-006**: 若模型載入或切換失敗，系統 MUST 顯示中文錯誤訊息，且 MUST 不影響服務整體可用性。
- **FR-007**: 若切換至新模型失敗，系統 MUST 能回退至先前可用模型以繼續提供翻譯服務（若先前存在可用模型）。
- **FR-008**: 系統狀態頁面與其相依資料取得（若有） MUST 不要求管理者權限；未登入使用者也 MUST 可存取。
- **FR-009**: 系統 MUST 提供可建置的容器映像，且使用者 MUST 能以 Podman 或 Docker 完成建置與啟動。
- **FR-010**: 容器啟動後 MUST 對外提供 HTTP 服務並提供健康檢查網址，供使用者確認服務可用。
- **FR-011**: 專案 MUST 提供 Compose 一鍵啟動方式，啟動後服務 MUST 可用並通過健康檢查。

### Assumptions

- 模型檔案已存在於模型目錄中（本功能不涵蓋模型下載/取得流程）。
- 「可用模型清單」預設列出所有符合最低判定條件的子目錄（不採白名單限制）。
- 模型選擇以「每位使用者的瀏覽器會話」為單位互不影響；若未明確選擇，使用系統預設模型。

### Key Entities *(include if feature involves data)*

- **Model**: 代表一個可被選擇的模型（識別為模型目錄名稱），包含可用狀態與（若失敗）錯誤訊息。
- **Model Selection**: 代表使用者目前選定的模型（與使用者會話關聯），影響後續翻譯請求的結果來源。

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: 在服務啟動後 60 秒內，使用者於翻譯頁面可看到可用模型清單（或明確的「無可用模型」提示）。
- **SC-002**: 使用者在 30 秒內可完成一次「切換模型→送出翻譯→取得結果」的完整流程（在硬體允許且模型可用情況下）。
- **SC-003**: 未登入使用者可在 3 秒內開啟系統狀態頁，且不會遇到權限錯誤（401/403）。
- **SC-004**: 使用者可在 10 分鐘內完成「建置映像並以容器工具啟動服務」且健康檢查成功（以新環境首次操作為基準）。
