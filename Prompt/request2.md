
# 多國語言翻譯系統 - 需求文件（擴充：模型切換 & 狀態頁免權限）

**版本**: 1.0
**日期**: 2026年1月21日
**範圍**: 既有專案功能擴充（Django ASGI + HTMX + Alpine.js）

---

## 一、背景與目標

### 1.1 背景
目前系統以既有模型運作，需擴充支援 `Translategemma-4b-it` 與 `Translategemma-12b-it`，並讓使用者可在網頁上切換使用模型。同時，系統狀態檢視頁面不應再受 Admin 權限控管，改為所有使用者皆可直接檢視。

### 1.2 目標
1. 啟動服務時自動掃描可用模型，並在網頁提供「模型選擇」以切換。
2. 系統狀態檢視（監控頁面）取消 Admin 權限限制，所有使用者可使用。

### 1.3 不在本次範圍（Out of Scope）
- 不要求新增/改造模型權重檔下載流程（假設模型已存在於 `models/` 目錄）。
- 不要求新增使用者登入、SSO、RBAC 等權限系統。
- 不要求調整語言清單與翻譯提示詞策略（除非為支援模型必要）。

---

## 二、核心需求

### 2.1 模型支援與啟動掃描（優先級：P1 - 必須）

#### 功能描述
- 系統啟動時，掃描 `models/` 目錄下的子目錄，找出「可用模型」。
- 可用模型清單提供給前端 UI 作為選項來源。
- 必須至少支援並可辨識以下模型目錄（以目錄名稱為準）：
	- `Translategemma-4b-it`
	- `Translategemma-12b-it`

#### 可用模型判定規則
為避免誤列空資料夾，啟動掃描時需符合以下條件才視為「可用」：
- 子目錄存在且可讀取
- 子目錄內至少包含 `config.json`（其餘檔案由現行載入流程決定；若載入失敗需在 UI 顯示錯誤，見 2.3）

> 註：本規格不限制模型格式（`.safetensors`/index 等）與 tokenizer 型式，實作以現有模型載入器可成功載入為準。

#### 驗收標準（Acceptance Scenarios）
1. **Given** `models/Translategemma-4b-it/config.json` 存在且可讀取，**When** 服務啟動完成，**Then** 模型下拉選單包含 `Translategemma-4b-it` 選項。
2. **Given** `models/Translategemma-12b-it/config.json` 存在且可讀取，**When** 服務啟動完成，**Then** 模型下拉選單包含 `Translategemma-12b-it` 選項。
3. **Given** `models/SomeEmptyDir/` 為空資料夾或缺少 `config.json`，**When** 服務啟動完成，**Then** 模型下拉選單不顯示 `SomeEmptyDir`。

---

### 2.2 前端模型切換（優先級：P1 - 必須）

#### 功能描述
- 翻譯頁面提供「模型選擇」元件（例如下拉選單）。
- 選項文字必須使用模型的**目錄名稱**作為顯示名稱（不可自行改名或硬編碼別名）。
- 使用者切換模型後，後續翻譯請求使用該模型進行推論。

#### UI/UX 規格
- 頁面初始載入時：
	- 若掃描到至少 1 個可用模型，預設選取第一個（或沿用系統既有預設模型機制；需在實作文件/設定中明確）。
	- 若未掃描到任何可用模型，顯示明確提示（例如「未偵測到可用模型，請確認 models/ 目錄」），並禁用翻譯按鈕。
- 切換模型時：
	- UI 顯示「切換中/載入中」狀態（避免使用者誤以為卡住）。
	- 若切換需要時間，應避免讓頁面無回應（可用 loading、禁用按鈕、或 toast 訊息）。

#### 行為規格（不限定實作，但需滿足結果）
- 模型切換可為「按需載入」或「預先載入」，但必須：
	- 切換成功後可立即用新模型翻譯
	- 切換失敗時不應影響系統穩定性（不可導致服務整體崩潰）
	- 切換失敗時應保留先前可用模型（若有）作為回退

#### 驗收標準（Acceptance Scenarios）
1. **Given** 使用者在翻譯頁且模型清單至少包含 A、B，**When** 使用者選擇模型 B 並執行翻譯，**Then** 該次翻譯使用模型 B 的推論結果回傳。
2. **Given** 使用者正在切換模型，**When** 模型尚未就緒，**Then** 翻譯按鈕為禁用狀態且畫面顯示載入提示。

---

### 2.3 模型載入/切換錯誤處理（優先級：P1 - 必須）

#### 功能描述
- 若模型目錄存在但實際載入失敗（格式不符、檔案缺失、GPU/CPU 記憶體不足等），需以使用者可理解的方式提示。

#### 驗收標準（Acceptance Scenarios）
1. **Given** 模型 `X` 出現在下拉選單但載入時發生錯誤，**When** 使用者切換到 `X`，**Then** 顯示錯誤訊息（中文）且系統不崩潰。
2. **Given** 系統原本使用模型 `A` 正常，**When** 切換到 `X` 失敗，**Then** 系統仍可回到模型 `A` 繼續翻譯。

---

## 三、系統狀態檢視取消 Admin 權限（優先級：P1 - 必須）

### 3.1 功能描述
- 「系統狀態/監控」頁面與其相依的資料取得端點（若有）不得要求 Admin 權限。
- 所有人（不需登入、不需 Admin）皆可直接查看系統狀態資訊。

### 3.2 驗收標準（Acceptance Scenarios）
1. **Given** 使用者未登入且無任何權限資訊，**When** 訪問系統狀態頁面，**Then** 頁面可正常顯示（HTTP 200）。
2. **Given** 使用者未登入且無任何權限資訊，**When** 狀態頁面向後端讀取狀態資料（若為 API），**Then** 資料可正常取得（HTTP 200），不得回傳 401/403。

---

## 四、相容性與限制

### 4.1 相容性
- 不破壞既有翻譯流程：若使用者不更動模型選擇，翻譯行為應與既有預設一致。

### 4.2 既知限制（允許但需呈現）
- 模型切換可能耗時（視模型大小與硬體），需在 UI 呈現載入狀態。

---

## 五、待確認事項（可在實作前決策）

1. 模型切換影響範圍：
	 - A) 每位使用者（瀏覽器會話）各自選擇模型（建議）
	 - B) 伺服器端全域單一 active model（節省資源，但會互相影響）
2. 「可用模型」掃描是否僅限特定白名單（例如只列出 Translategemma*），或列出所有符合條件的目錄。

---

## 六、Docker Image 產出（Podman / Docker 可直接啟動）（優先級：P1 - 必須）

### 6.1 目標
- 產出可建置的容器映像，使用者可用 Podman 或 Docker 在本機直接啟動服務，不依賴額外腳本。
- 容器啟動後需可對外提供 HTTP 服務（預設連接埠 8000），並支援既有健康檢查端點。

### 6.2 建置規格
- 必須提供容器建置檔：`Containerfile`（沿用現有專案檔名）。
- 必須同時支援以下兩種建置方式（擇一工具即可完成建置）：
	- Podman：`podman build -t <image> -f Containerfile .`
	- Docker：`docker build -t <image> -f Containerfile .`
- 必須提供 Docker Compose 啟動方式（沿用現有 `docker-compose.yaml` 檔名），可一鍵啟動服務。

### 6.3 執行規格
- 容器需對外暴露並監聽 `8000/tcp`。
- 容器啟動命令需可直接啟動 ASGI 服務（例如 uvicorn），並以 `0.0.0.0:8000` 對外提供服務。
- 模型檔不要求打包進映像；必須支援以 volume 掛載方式提供模型（唯讀），掛載路徑為 `/app/models`。
- 必須支援掛載 `config/`（唯讀）與 `logs/`（可寫），以符合既有專案目錄慣例：
	- `./models:/app/models:ro`
	- `./config:/app/config:ro`
	- `./logs:/app/logs`

### 6.4 健康檢查
- 容器啟動後，必須可透過 `GET /api/health/` 進行健康檢查。

### 6.5 驗收標準（Acceptance Scenarios）
1. **Given** 專案根目錄存在 `Containerfile`，**When** 執行 `podman build -t translation-service -f Containerfile .`，**Then** 映像建置成功。
2. **Given** 專案根目錄存在 `Containerfile`，**When** 執行 `docker build -t translation-service -f Containerfile .`，**Then** 映像建置成功。
3. **Given** 主機端已準備 `./models` 目錄，**When** 執行容器（`-p 8000:8000 -v ./models:/app/models:ro`），**Then** `http://localhost:8000/api/health/` 回傳 HTTP 200。
4. **Given** 掛載 `./config` 與 `./logs`，**When** 容器執行一段時間，**Then** 服務可正常運作且日誌可寫入 `./logs`（不得因權限問題導致服務啟動失敗）。
5. **Given** 專案根目錄存在 `docker-compose.yaml`，**When** 執行 `docker compose -f docker-compose.yaml up -d`（或 `docker-compose up -d`），**Then** `http://localhost:8000/api/health/` 回傳 HTTP 200。

