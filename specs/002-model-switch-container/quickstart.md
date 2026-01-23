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
