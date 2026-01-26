# Phase 1 - Data Model

本功能主要以「模型目錄掃描 + 使用者選擇 + 模型載入狀態」為核心；資料多為「即時狀態」與「會話偏好」，不新增傳統資料庫表。

## Entity：ModelEntry

代表一個可被列入清單的模型（以 `models/<model_id>/` 目錄表示）。

- 主鍵
  - `model_id: string`（= 目錄名稱；顯示名稱也必須一致）

- 欄位
  - `path_rel: string`（例如 `models/Translategemma-4b-it`）
  - `has_config: bool`（是否存在 `config.json`；此為列入清單的最低門檻）
  - `is_readable: bool`（目錄/檔案可讀取）
  - `last_error_message?: string`（最近一次載入失敗原因；中文可理解訊息）

- 驗證規則
  - `model_id` 必須是單一資料夾名稱，不允許 `..`、`/`、`\`、絕對路徑等（避免路徑穿越）。

## Entity：ModelRuntimeState（全域）

代表伺服器端目前推論模型的即時狀態（單例）。

- 欄位
  - `active_model_id?: string`（目前已載入並作為 active 的模型；若尚未載入則為 null）
  - `status: string`（對應現有 `ModelStatus`：`not_loaded`/`loading`/`loaded`/`error`）
  - `execution_mode: string`（`gpu`/`cpu`/`remote`；沿用現有 `ModelService.get_execution_mode()`）
  - `loading_progress: number`（0-100）
  - `error_message?: string`

- 狀態轉換
  - `not_loaded` → `loading` → `loaded`
  - `loading` → `error`
  - `loaded` → `loading`（切換模型時）
  - `error` → `loading`（重新嘗試載入）

## Entity：ModelSelection（每瀏覽器會話）

代表使用者在翻譯頁的模型偏好。

- 儲存位置
  - 預設：前端 `sessionStorage`（符合既有偏好設定保存方式）
  - 可選：Django session（server-side），用於多分頁一致性或未來擴充

- 欄位
  - `selected_model_id?: string`
  - `updated_at?: string (ISO 8601)`（前端可選，用於除錯顯示）

- 行為
  - 若 `selected_model_id` 為空：使用「系統預設模型」或清單第一個可用模型。

## Entity：PublicStatusSnapshot（只讀 API 回應）

狀態頁用的彙總快照，目標是讓匿名使用者也能讀取。

- 欄位（建議沿用既有 `admin_status` schema，減少前端改動）
  - `status: "ok" | "error"`
  - `timestamp: string`
  - `system: object`
  - `resources: { cpu, memory, gpu, disk }`
  - `uptime: object`
  - `model: { loaded: bool, name?: string, execution_mode?: string, active_model_id?: string }`
  - `queue: object`

## Notes

- 本次不引入 DB migration；所有狀態可由既有 service 即時計算/快取。
- 若未來要支援多模型同時常駐（LRU cache），可新增 `LoadedModelCacheEntry` 概念，但本次不做實作承諾，僅保留設定擴充點。
