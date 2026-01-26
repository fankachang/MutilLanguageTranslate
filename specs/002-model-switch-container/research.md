# Phase 0 - Research

本文件用於消除規格中的待確認事項與技術選型不確定性，並以「Decision / Rationale / Alternatives considered」格式記錄。

## Decision 1：模型切換影響範圍採「每瀏覽器會話選擇 + 伺服器端單一 active model（可回退）」

- Decision：
  - 使用者的「選定模型」以 Django session（或前端 sessionStorage）記錄，達成「每瀏覽器會話」互不影響的偏好保存。
  - 伺服器端推論資源採現有 `ModelService` 單例模型：同時間維持單一 active model（避免同時常駐多個大型模型造成 OOM）。
  - 若翻譯請求指定的模型 ≠ active model，翻譯服務會先嘗試切換（或拒絕並要求先切換），切換失敗必須回退到先前 active model。

- Rationale：
  - 現有架構已明確是單例 `ModelService` + 單一 `LocalModelProvider`（單一 `model/tokenizer`）；直接擴成多模型常駐會有高風險與高複雜度。
  - 規格允許「按需載入」；以 session 記錄偏好能滿足「每會話選擇」的需求，而推論層仍可保持最小可行與可維運。

- Alternatives considered：
  - A) 每使用者都常駐自己的模型：資源不可行（GPU/CPU 記憶體爆炸），且會引入複雜的生命週期管理。
  - B) 完全全域單一選擇（所有使用者共用同一模型且無會話偏好）：雖最省資源，但不符合需求文件「建議每位使用者可選」。
  - C) 多模型快取（LRU 1..N）：可作為未來擴充，但本次先設計「可配置上限」並預設 1，以避免過度設計。

## Decision 2：可用模型掃描規則採「models/*/config.json 存在」作為最低門檻

- Decision：
  - 啟動時（或首次請求時）掃描 `settings.MODELS_DIR` 下一層子目錄。
  - 子目錄存在且可讀取、且包含 `config.json` → 列入可用模型清單；缺少 `config.json` → 不列出。

- Rationale：
  - 完全符合規格的最低門檻，避免空資料夾誤列。
  - 不把更多檔案條件硬編碼，避免限制模型格式（safetensors/index/tokenizer 形式可能不同）。

- Alternatives considered：
  - 以 `tokenizer.json`、`model.safetensors.index.json` 等更嚴格條件判定：會誤排除可被 transformers 載入的模型，且違反規格「以現行載入流程可成功載入為準」。

## Decision 3：狀態頁與資料 API 去權限化採「新增 public 只讀端點」

- Decision：
  - 保留既有 `/api/v1/admin/*` 白名單保護，避免影響具副作用的管理功能（例如觸發載入/測試模型）。
  - 新增 public 只讀端點（不在 `/api/v1/admin/` 命名空間），供狀態頁讀取：
    - `GET /api/v1/status/`
    - `GET /api/v1/statistics/`
    - `GET /api/v1/model/load-progress/`
  - 狀態頁模板改以 public 端點抓資料，確保未登入/非白名單也能 `HTTP 200`。

- Rationale：
  - 目前 IP 白名單中介軟體是以路徑前綴 `/api/v1/admin/` 做保護；狀態頁模板目前直接 fetch 這些端點，導致非白名單情境必然 403。
  - 以新增 public endpoint 的方式不破壞既有 admin API 的語意與安全邊界，風險最低。

- Alternatives considered：
  - 在 IP 白名單中介軟體對部分 admin 端點做例外放行：改動雖小，但會讓 `/api/v1/admin/*` 的安全邊界變得不一致，未來容易踩雷。

## Decision 4：翻譯 API 與前端整合採「translate request 可選帶 model_id」

- Decision：
  - `POST /api/v1/translate/` 增加可選欄位 `model_id`（不帶則維持現有預設行為）。
  - 前端翻譯頁以 sessionStorage 保存使用者選定模型；送出翻譯時附帶 `model_id`。

- Rationale：
  - 不破壞既有 client（向後相容）。
  - 前端已大量使用 sessionStorage 保存設定；用相同機制保存 model_id 最簡單。

- Alternatives considered：
  - 只用 server-side session：也可行，但需要更明確的選擇 API 與 session 寫入流程；本次以「前端帶參數」為主，server-side session 可作為後續加值。

## Decision 5：容器啟動命令避免硬依賴 uvloop

- Decision：
  - 容器啟動若要指定 `--loop uvloop`，需確保 `uvloop` 在 requirements 且平台可用；否則應移除此參數使用 uvicorn 預設 loop。

- Rationale：
  - 目前 requirements 未明確包含 `uvloop`，但 Containerfile 指定 `--loop uvloop`，在乾淨環境有機率啟動失敗；這會直接影響 P1 的容器驗收。

- Alternatives considered：
  - 加入 `uvloop` 依賴：Linux 上可行，但要注意與 windows 開發環境差異；若無明確效益與測試，先不強制。
