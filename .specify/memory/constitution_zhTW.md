<!--
注意：此文件為 .specify/memory/constitution.md 的繁體中文翻譯版。
版本：1.1.0 | 制定：2026-01-08 | 最後修訂：2026-01-21
若翻譯與英文原文有衝突，以英文原文為準。
-->

# TAIDE 翻譯系統憲章（翻譯版）

## 核心原則

### I. 離線優先架構（Offline-First Architecture）
所有系統元件必須能在完全隔離的內網環境中運作，且不依賴外部網路連線。包含但不限於：
- 模型部署：所有 AI 模型必須可本機部署，不得呼叫外部 API
- 依賴管理：所有依賴（函式庫、框架、靜態資產）必須可離線取得
- 自包含：不得依賴外部 CDN、雲端服務或遠端資源

### II. 效能即功能（Performance as a Feature）
翻譯效能是核心使用者體驗指標，非可選項：
- GPU 模式：1000 字元翻譯目標 2–3 秒（p95）
- CPU 模式：1000 字元翻譯目標 8–10 秒（p95）
- 併發：支援 100 位同時使用者且不顯著劣化
- 所有架構決策必須考量效能影響並能說明理由

### III. 簡單務實（Simplicity and Pragmatism）（不可妥協）
避免過度工程化。除非能證明必要，否則優先選擇更簡單的方案：
- YAGNI 原則：只在確定需要時才實作，不做推測性功能
- 能用 Django 內建就不要引入重複功能的第三方套件
- 不要在 HTMX/Alpine.js 足夠時引入大型前端框架（React/Vue）
- 每新增一個依賴都必須回答：「能不能用既有工具達成？」

### IV. 測試驅動開發（Test-Driven Development）
測試是必須，不是可選：
- 單元測試：所有商業邏輯必須有單元測試覆蓋
- 整合測試：API 合約必須以整合測試驗證
- 效能測試：若宣稱 100+ 併發能力，必須有負載測試驗證
- 測試結構：tests/unit/、tests/integration/、tests/performance/
- 線上系統紀律：修 bug 或調整行為時，必須先寫會失敗的回歸測試
- Red/Green：變更前測試必須先失敗，修正後才通過

### V. 可觀測性與可維護性（Observability and Maintainability）
系統必須可除錯且可在正式環境維護：
- 結構化日誌：三層級（ERROR/WARNING/INFO）並保留 30 天
- 監控：提供系統狀態 API，揭露資源使用、錯誤統計、併發指標
- 健康檢查：提供 /api/health 端點供監控工具使用
- 錯誤脈絡：所有錯誤需包含可行動資訊（request_id、error_code、建議解法）

### VI. 設定優於程式碼（Configuration Over Code）
設定必須外部化並可因環境調整：
- YAML 設定：config/app_config.yaml、config/model_config.yaml、config/languages.yaml
- 不得硬編碼：資源限制、逾時、路徑等必須可設定
- 合理預設：最少設定即可開箱可用
- 文件化：所有設定選項必須記錄在 quickstart.md

### VII. API 優先設計（API-First Design）
對外介面（API）是合約，必須保持穩定：
- RESTful 原則：遵循 HTTP method、status code、資源命名慣例
- Schema 驗證：所有 request/response 格式必須明確定義
- 錯誤一致性：所有端點使用一致的錯誤碼與錯誤格式
- 向後相容：破壞性變更（包含重新命名/移除）必須提升 major 版號並提供遷移指南

### VIII. 介面一致性與命名穩定（Interface Integrity & Identifier Stability）
本專案為已上線系統；整合正確性與穩定性不可妥協：
- 不得任意重新命名函式、變數、類別、路由、模板 ID、設定鍵
- 只有在功能需求或 bug 修正「必須」的情況下才能改名，且必須：
	- 更新所有呼叫端
	- 若屬公開合約的一部分，需維持向後相容
	- 若無法維持相容，需提供遷移說明
- 禁止臆測介面：前端只能呼叫實際存在的後端端點/函式
- 新增呼叫前，必須先確認後端路由/函式已實作並完成串接（例如 urls.py）

## 其他限制

### 技術棧要求
- **語言**：Python 3.11+（不支援 Python 2.x，需強制最低版本）
- **框架**：Django 4.2+（ASGI）
- **AI 模型**：TAIDE-LX-7B-Chat（僅限本機部署）
- **前端**：優先採伺服端渲染模板，避免 SPA
- **資料庫**：除非能說明必要性，避免 PostgreSQL/MySQL；僅允許以 SQLite 作為任務佇列等用途

### 安全性要求
- **驗證**：內網部署可不需驗證，但系統需能為未來整合驗證預留空間
- **輸入驗證**：所有使用者輸入必須於後端驗證（不可只依賴前端驗證）
- **速率限制**：即使在內網也需防濫用（以 IP 為基礎的 rate limiting）
- **檔案上傳**：批次翻譯上傳需嚴格限制檔案類型與大小

### 部署限制
- **內網環境**：部署與運作不得依賴網際網路
- **單機部署**：初期以單機為目標（避免分散式系統）
- **資源隔離**：GPU 記憶體使用需限制以避免 OOM（最大 0.8 fraction）
- **優雅降級**：GPU 不可用時必須自動回退至 CPU 模式

## 開發流程

### Code Review 要求
- **先自我審查**：作者在送審前需先自行檢查
- **憲章遵循**：審查者必須確認變更符合所有原則
- **測試覆蓋**：新功能必須附帶相對應測試（不可「只寫程式不寫測試」）
- **文件更新**：影響 API 或設定的變更，必須更新相關文件

### Git Commit 規範
- **語言**：所有 commit message、程式註解、文件必須使用繁體中文（zh-TW）
- **格式**：遵循 Conventional Commits（feat/fix/docs/refactor/test）
- **範圍**：包含 feature branch 前綴（例如："feat(001-taide-translation): 新增即時翻譯 API"）
- **內容**：解釋 WHY，而不只是 WHAT（必要時連結 spec.md 或 issue）

### 測試門檻（Gates）
- **Pre-commit**：提交前本機 unit tests 必須通過
- **Pre-push**：推送前 unit + integration 必須通過
- **Pre-deploy**：上線前需以效能測試驗證併發目標
- **回歸**：破壞性變更需明確核准並提供遷移文件

## 治理

### 憲章權威
- 本憲章高於其他開發慣例與指引
- 便利性與憲章衝突時，以憲章為準
- 例外必須明確記錄並取得團隊共識

### 修訂流程
- 修訂需在 constitution.md 記錄並說明理由
- 若對原則做破壞性調整，需提供既有程式碼的遷移計畫
- 每次修訂必須更新版本與修訂日期

### 複雜度正當性
- 若違反「簡單務實」，需在 plan.md 的「Complexity Tracking」記錄
- 理由需包含：(1) 為何需要、(2) 為何不採用更簡單替代方案
- 例：新增第 4 個服務、在直連 DB 足夠時引入 Repository pattern

### 執行與落實
- 所有 code review 必須檢查憲章遵循
- CI/CD 盡可能自動化檢查（lint、測試覆蓋等）
- 參考 AGENTS.md 以取得 agent 相關的開發指引
