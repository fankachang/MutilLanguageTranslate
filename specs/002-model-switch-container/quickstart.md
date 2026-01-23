# Phase 1 - Quickstart（模型切換 / 公開狀態頁 / 容器）

本文件描述本次功能擴充的使用方式與驗證步驟，著重在「可用模型掃描、模型切換流程、狀態頁匿名可用、容器啟動與健康檢查」。

## 先決條件

- Python 3.11（建議）
- 已準備模型資料夾於 `models/`（本次不涵蓋模型下載）

## 模型目錄準備

可用模型最低門檻：

- `models/<model_id>/config.json` 存在且可讀取

範例：

```text
models/
├── Translategemma-4b-it/
│   └── config.json
└── Translategemma-12b-it/
    └── config.json
```

## 本機啟動（開發）

```powershell
# 進入 Django 專案
cd D:\Project\MutilLangTranslate\translation_project

# 啟動（Django runserver）
..\.venv\Scripts\python manage.py runserver
```

開啟：

- 翻譯頁：`http://localhost:8000/`
- 狀態頁：`http://localhost:8000/admin/status/`（本次需求：未登入也可開啟，且其資料 API 不應回 401/403）

## API 驗證

### 1) 取得可用模型清單

`GET http://localhost:8000/api/v1/models/`

### 2) 設定本會話選定模型

`PUT http://localhost:8000/api/v1/models/selection/`

Body：

```json
{ "model_id": "Translategemma-4b-it" }
```

### 3) 觸發切換 active model（含回退）

`POST http://localhost:8000/api/v1/models/switch/`

Body：

```json
{ "model_id": "Translategemma-12b-it" }
```

### 4) 公開狀態 API（匿名可用）

- `GET http://localhost:8000/api/v1/status/`
- `GET http://localhost:8000/api/v1/statistics/`
- `GET http://localhost:8000/api/v1/model/load-progress/`

### 5) 翻譯（可選指定 model_id）

`POST http://localhost:8000/api/v1/translate/`

Body：

```json
{
  "text": "Hello",
  "source_language": "auto",
  "target_language": "zh-TW",
  "quality": "standard",
  "model_id": "Translategemma-4b-it"
}
```

## 容器啟動（Podman / Docker / Compose）

> 本次驗收重點：容器啟動後 `GET /api/health/` 必須回 200。

備註：Containerfile 的啟動方式使用 `uvicorn` 預設 event loop（不強制 `uvloop`），避免在乾淨環境因缺少 uvloop 而啟動失敗。

### Podman

```bash
podman build -t translation-service -f Containerfile .

podman run -d \
  --name translation-service \
  -p 8000:8000 \
  -v ./models:/app/models:ro \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  translation-service
```

### Docker

```bash
docker build -t translation-service -f Containerfile .

docker run -d \
  --name translation-service \
  -p 8000:8000 \
  -v ./models:/app/models:ro \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  translation-service
```

### Docker Compose

```bash
docker compose -f docker-compose.yaml up -d
```

### 健康檢查

```bash
curl -f http://localhost:8000/api/health/
```

## 常見情境

- **無可用模型**：若 `models/` 下沒有任何包含 `config.json` 的子目錄，翻譯頁應顯示明確提示並禁用翻譯。
- **切換中**：切換模型尚未完成時，翻譯按鈕應禁用並顯示載入/切換中狀態。
- **切換失敗**：切換失敗時需顯示中文錯誤訊息，且系統應回退到先前可用模型（若存在）。

## 端到端驗證與驗收量測（SC-001 ~ SC-004）

本段落目的：提供「可重現」的量測方式。由於模型大小與硬體差異很大，若時間門檻不穩定，至少要能在目標環境以相同步驟重跑並取得量測數據。

### 需要記錄的環境條件（請在目標環境填寫）

- OS：Windows / Linux / macOS（版本）
- CPU：型號 / 核心數
- RAM：容量
- GPU：型號 / VRAM（若有）
- Python：版本（本專案建議 3.11）
- 容器工具：Docker / Podman 版本（若使用容器驗收）
- 模型：本次掛載的 `models/<model_id>` 清單（至少要包含 `config.json`）

本次倉庫內快速驗證（功能面；不等同於時間門檻量測）：

- OS：Windows（pytest 輸出 `platform win32`）
- Python：3.10.11
- Django：5.2.10
- pytest：9.0.2
- 執行指令：`D:\Project\MutilLangTranslate\.venv\Scripts\python -m pytest`
- 結果：`55 passed, 3 skipped`（performance tests 需伺服器運行而跳過）

### SC-001：啟動後 60 秒內可看到模型清單或「無可用模型」提示

量測方式（本機啟動後）：

```powershell
Measure-Command { curl -s -o $null http://localhost:8000/api/v1/models/ }
curl -s http://localhost:8000/api/v1/models/
```

驗收重點：

- 翻譯頁 `/` 能在 UI 顯示模型選項；若沒有任何模型，UI 需顯示「未偵測到可用模型」並禁用翻譯。

### SC-002：30 秒內完成「切換模型 → 送出翻譯 → 取得結果」

注意：首次切換大模型通常會超過 30 秒（載入/權重映射耗時），建議在「模型已可用且硬體允許」的目標環境做量測。

量測方式（以 API 驗證流程；可搭配碼表或 PowerShell 計時）：

```powershell
# 1) 設定本會話選定模型
Measure-Command {
  curl -s -X PUT http://localhost:8000/api/v1/models/selection/ -H "Content-Type: application/json" -d '{"model_id":"<model_id>"}' | Out-Null
}

# 2) 觸發切換 active model
Measure-Command {
  curl -s -X POST http://localhost:8000/api/v1/models/switch/ -H "Content-Type: application/json" -d '{"model_id":"<model_id>","force":false}' | Out-Null
}

# 3) 送出翻譯（可選帶 model_id）
Measure-Command {
  curl -s -X POST http://localhost:8000/api/v1/translate/ -H "Content-Type: application/json" -d '{"text":"Hello","source_language":"auto","target_language":"zh-TW","quality":"standard","model_id":"<model_id>"}' | Out-Null
}
```

### SC-003：未登入使用者 3 秒內可開啟狀態頁且不遇到 401/403

量測方式：

```powershell
Measure-Command { curl -s -o $null -I http://localhost:8000/admin/status/ }
curl -s -o $null -w "status=%{http_code} time_total=%{time_total}\n" http://localhost:8000/api/v1/status/
```

驗收重點：

- `/admin/status/` 匿名回 200
- `/api/v1/status/`、`/api/v1/statistics/`、`/api/v1/model/load-progress/` 匿名回 200

### SC-004：10 分鐘內完成容器建置與啟動並通過健康檢查

量測方式（Docker Compose 範例）：

```bash
# 計時開始（可用碼表）
docker compose -f docker-compose.yaml up -d --build
curl -f http://localhost:8000/api/health/
# 計時結束
```

驗收重點：

- 容器啟動後 `GET /api/health/` 回 200
- 主機 `./models` 建議以唯讀掛載到容器 `/app/models:ro`，避免容器寫入模型檔案
