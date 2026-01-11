# 快速入門：多國語言翻譯系統

**功能分支**: `001-multilang-translation`  
**建立日期**: 2026-01-11

## 系統需求

### 硬體需求

| 項目 | 最低需求 | 建議配置 |
|------|----------|----------|
| CPU | 8 核心 | 16 核心 |
| RAM | 16 GB | 32 GB |
| GPU | - | NVIDIA GPU (12GB+ VRAM) |
| 儲存空間 | 50 GB | 100 GB SSD |

### 軟體需求

| 軟體 | 版本 |
|------|------|
| Python | 3.11+ |
| CUDA (選用) | 12.0+ |
| Podman (選用) | 4.0+ |

---

## 專案結構

```
MutilLangTranslate/
├── translation_project/          # Django 專案根目錄
│   ├── manage.py
│   ├── translation_project/      # Django 專案設定
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   │
│   └── translator/               # Django 應用程式
│       ├── api/                  # REST API
│       ├── services/             # 商業邏輯
│       ├── middleware/           # 中介軟體
│       ├── templates/            # Django Templates
│       └── static/               # 靜態檔案
│
├── config/                       # 配置檔案
│   ├── app_config.yaml
│   ├── model_config.yaml
│   └── languages.yaml
│
├── logs/                         # 日誌目錄
│
├── models/                       # TAIDE-LX-7B 模型檔案
│   └── models--taide--TAIDE-LX-7B/
│
├── tests/                        # 測試
│   ├── unit/
│   ├── integration/
│   └── performance/
│
└── specs/                        # 規格文件
    └── 001-multilang-translation/
```

---

## 環境設定

### 1. 克隆專案

```bash
git clone <repository-url>
cd MutilLangTranslate
git checkout 001-multilang-translation
```

### 2. 建立 Python 虛擬環境

```bash
# 建立虛擬環境
python -m venv venv

# 啟用虛擬環境 (Windows)
.\venv\Scripts\activate

# 啟用虛擬環境 (Linux/Mac)
source venv/bin/activate
```

### 3. 安裝依賴套件

```bash
pip install -r requirements.txt
```

**requirements.txt 主要內容**：
```
Django>=4.2,<5.0
uvicorn[standard]>=0.24.0
transformers>=4.36.0
torch>=2.1.0
PyYAML>=6.0
psutil>=5.9.0
```

### 4. 配置檔案設定

複製範本並修改配置：

若專案提供 `.example` 範本檔案，可先複製後再修改；若沒有範本，請直接建立 `config/app_config.yaml` 與 `config/model_config.yaml`。

```bash
# Linux/Mac（或 Git Bash）
cp config/app_config.yaml.example config/app_config.yaml
cp config/model_config.yaml.example config/model_config.yaml
```

```powershell
# Windows PowerShell
Copy-Item config/app_config.yaml.example config/app_config.yaml
Copy-Item config/model_config.yaml.example config/model_config.yaml
```

**config/app_config.yaml 關鍵配置**：

```yaml
# 應用程式配置
app:
  debug: false
  timeout_seconds: 120

# 翻譯配置
translation:
  max_text_length: 10000
  max_concurrency: 100
  max_queue_size: 100
  default_quality: standard

# 安全配置
security:
  internal_ip_ranges:
    - "192.168.0.0/16"
    - "10.0.0.0/8"
    - "172.16.0.0/12"
    - "127.0.0.1/32"
  admin_ip_ranges:
    - "192.168.1.100/32"

# 日誌配置
logging:
  retention_days: 30
  log_directory: "logs"
```

**config/model_config.yaml 關鍵配置**：

```yaml
model:
  path: "models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979"
  device: auto  # auto, cuda, cpu
  max_memory:
    0: "12GiB"  # GPU 記憶體限制
  
quality_settings:
  fast:
    temperature: 0.7
    top_p: 0.9
    num_beams: 1
    max_new_tokens: 512
  standard:
    temperature: 0.5
    top_p: 0.85
    num_beams: 2
    max_new_tokens: 1024
  high:
    temperature: 0.3
    top_p: 0.8
    num_beams: 4
    max_new_tokens: 2048
```

---

## 啟動服務

### 1. 初始化 Django

```bash
cd translation_project
python manage.py migrate --run-syncdb
python manage.py collectstatic --noinput
```

### 2. 啟動開發伺服器

```bash
# 使用 uvicorn（ASGI，建議）
uvicorn translation_project.asgi:application --host 0.0.0.0 --port 8000

# 或使用 Django 開發伺服器（僅開發用）
python manage.py runserver 0.0.0.0:8000
```

應用程式將在 `http://localhost:8000` 啟動。

### 3. 驗證服務

```bash
# 健康檢查
curl http://localhost:8000/api/health/

# 取得語言清單
curl http://localhost:8000/api/v1/languages/

# 執行翻譯
curl -X POST http://localhost:8000/api/v1/translate/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World", "target_language": "zh-TW"}'
```

---

## 開發模式

### 熱重載

```bash
# 使用 uvicorn 熱重載
uvicorn translation_project.asgi:application --reload --port 8000

# 或使用 Django runserver（自動熱重載）
python manage.py runserver
```

### 執行測試

```bash
# 單元測試
pytest tests/unit/

# 整合測試
pytest tests/integration/

# 全部測試
pytest

# 測試覆蓋率
pytest --cov=translator --cov-report=html
```

---

## 常見問題

### Q1: 模型載入失敗

確認模型檔案路徑正確：
```
models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979/
```

並確認有以下檔案：
- `config.json`
- `model-00001-of-00003.safetensors`
- `model-00002-of-00003.safetensors`
- `model-00003-of-00003.safetensors`
- `tokenizer.model`

### Q2: GPU 記憶體不足

調整 `config/model_config.yaml` 中的記憶體限制：
```yaml
model:
  max_memory:
    0: "10GiB"  # 減少 GPU 記憶體使用
```

或強制使用 CPU 模式：
```yaml
model:
  device: cpu
```

### Q3: 連線被拒絕 (403)

檢查 `config/app_config.yaml` 中的 IP 白名單配置，確認您的 IP 在允許範圍內。

開發環境下可暫時加入：
```yaml
security:
  internal_ip_ranges:
    - "0.0.0.0/0"  # 允許所有 IP（僅限開發環境！）
```

### Q4: 翻譯逾時

- 縮短輸入文字長度
- 檢查模型是否正常載入（查看 /api/health/）
- 調整 `timeout_seconds` 配置（預設 120 秒）

### Q5: ASGI 伺服器無法啟動

確認已安裝 uvicorn：
```bash
pip install uvicorn[standard]
```

---

## API 快速參考

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/translate/` | POST | 執行翻譯 |
| `/api/v1/translate/{id}/status/` | GET | 查詢狀態 |
| `/api/v1/languages/` | GET | 語言清單 |
| `/api/v1/admin/status/` | GET | 系統狀態* |
| `/api/v1/admin/statistics/` | GET | 統計資料* |
| `/api/health/` | GET | 健康檢查 |

*需 IP 白名單

---

## 生產部署

### 使用 Gunicorn + Uvicorn Workers

```bash
gunicorn translation_project.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  --bind 0.0.0.0:8000
```

### 使用 Podman 容器化部署

系統使用 Podman 作為容器引擎（Docker 相容）。

**建立 Containerfile**：

```dockerfile
# Containerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY translation_project/ ./translation_project/
COPY config/ ./config/

# 暴露端口
EXPOSE 8000

# 啟動指令
CMD ["uvicorn", "translation_project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
```

**建置映像**：

```bash
# 使用 Podman 建置
podman build -t translation-service:latest .

# GPU 支援版本（需安裝 nvidia-container-toolkit）
podman build -f Containerfile.gpu -t translation-service:gpu .
```

**執行容器**：

```bash
# CPU 模式
podman run -d \
  --name translation \
  -p 8000:8000 \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  -v ./models:/app/models:ro \
  translation-service:latest

# GPU 模式（需 nvidia-container-toolkit）
podman run -d \
  --name translation-gpu \
  --device nvidia.com/gpu=all \
  -p 8000:8000 \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  -v ./models:/app/models:ro \
  translation-service:gpu
```

**常用 Podman 指令**：

```bash
# 檢視運行中的容器
podman ps

# 檢視日誌
podman logs -f translation

# 停止容器
podman stop translation

# 移除容器
podman rm translation

# 進入容器除錯
podman exec -it translation /bin/bash
```

> **注意**：Podman 與 Docker 指令相容，可使用 `alias docker=podman` 簡化操作。

### 使用 systemd 服務

```ini
# /etc/systemd/system/translation.service
[Unit]
Description=Translation Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/MutilLangTranslate/translation_project
ExecStart=/path/to/venv/bin/gunicorn translation_project.asgi:application -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 下一步

1. 閱讀 [API 契約](contracts/api-contract.md) 了解完整 API 規格
2. 閱讀 [資料模型](data-model.md) 了解資料結構
3. 閱讀 [研究文件](research.md) 了解技術決策
