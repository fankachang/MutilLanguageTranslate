# 多國語言翻譯系統

基於 TAIDE-LX-7B 大型語言模型的多國語言翻譯系統，採用 Django ASGI + HTMX + Alpine.js 技術架構，提供即時翻譯、歷史記錄、使用者設定等功能。

## 功能特點

- 🌐 **多語言支援**：支援繁體中文、簡體中文、英文、日文、韓文、越南文、泰文、印尼文等 8 種語言
- 🔄 **自動語言偵測**：智慧偵測輸入文字的來源語言
- ⚡ **即時翻譯**：低延遲翻譯回應，支援 GPU 加速
- 📝 **翻譯歷史**：瀏覽器本地儲存，保留最近 20 筆翻譯記錄
- ⚙️ **個人化設定**：支援深色/淺色主題、字體大小調整
- 📊 **系統監控**：即時查看系統資源使用狀況和翻譯統計

## 系統需求

### 硬體需求

| 項目 | 最低需求 | 建議配置 |
|------|---------|---------|
| CPU | 4 核心 | 8 核心以上 |
| 記憶體 | 16 GB | 32 GB 以上 |
| GPU | - | NVIDIA GPU (16GB+ VRAM) |
| 磁碟 | 50 GB | 100 GB SSD |

### 軟體需求

- Python 3.11+
- CUDA 11.8+（GPU 加速時需要）
- Git

## 快速開始

### 1. 複製專案

```bash
git clone <repository-url>
cd MutilLanguageTranslate
```

### 2. 建立虛擬環境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. 安裝相依套件

```bash
pip install -r requirements.txt
```

### 4. 設定配置檔

```bash
# 複製範例配置檔
cp config/app_config.yaml.example config/app_config.yaml
cp config/model_config.yaml.example config/model_config.yaml

# 依據需求編輯配置檔
```

### 5. 下載模型

模型會在首次啟動時自動下載，或可手動下載：

```bash
# 模型將儲存於 models/ 目錄
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('taide/TAIDE-LX-7B', cache_dir='./models')"
```

### 6. 啟動服務

```bash
cd translation_project

# 開發模式
python manage.py runserver

# 生產模式（使用 uvicorn）
uvicorn translation_project.asgi:application --host 0.0.0.0 --port 8000
```

### 7. 開啟瀏覽器

造訪 http://localhost:8000 開始使用翻譯服務。

## 容器部署

### 使用 Podman

```bash
# 建置映像
podman build -t translation-service -f Containerfile .

# 執行容器
podman run -d \
  --name translation-service \
  -p 8000:8000 \
  -v ./models:/app/models:ro \
  -v ./logs:/app/logs \
  translation-service
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

## 目錄結構

```
MutilLanguageTranslate/
├── config/                    # 配置檔目錄
│   ├── app_config.yaml       # 應用程式配置
│   ├── model_config.yaml     # 模型配置
│   └── languages.yaml        # 語言定義
├── logs/                      # 日誌目錄
├── models/                    # 模型目錄
├── translation_project/       # Django 專案
│   ├── translation_project/  # 專案設定
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   └── translator/           # 翻譯應用程式
│       ├── api/              # REST API
│       ├── services/         # 服務層
│       ├── templates/        # 前端模板
│       ├── static/           # 靜態資源
│       └── utils/            # 工具函數
├── specs/                     # 規格文件
├── tests/                     # 測試
├── Containerfile             # 容器建置檔
├── docker-compose.yaml       # Docker Compose
├── requirements.txt          # Python 相依套件
└── README.md                 # 本文件
```

## API 文件

### 翻譯 API

#### POST /api/v1/translate/

執行文字翻譯。

**請求**
```json
{
  "text": "要翻譯的文字",
  "source_language": "auto",
  "target_language": "en",
  "quality": "standard"
}
```

**回應**
```json
{
  "request_id": "uuid",
  "status": "completed",
  "translated_text": "Translated text",
  "processing_time_ms": 1234.56,
  "detected_language": "zh-TW"
}
```

### 健康檢查 API

#### GET /api/health/

回傳系統健康狀態。

#### GET /api/ready/

就緒探針，檢查服務是否準備好接收流量。

#### GET /api/live/

存活探針，檢查服務是否存活。

### 語言 API

#### GET /api/v1/languages/

取得支援的語言清單。

## 配置說明

### app_config.yaml

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1

translation:
  default_source_language: "auto"
  default_target_language: "en"
  max_text_length: 5000
  timeout_seconds: 120

security:
  admin_ip_whitelist:
    - "127.0.0.1"
    - "::1"
```

### model_config.yaml

```yaml
model:
  name: "taide/TAIDE-LX-7B"
  cache_dir: "./models"
  device: "auto"  # auto, cuda, cpu
  torch_dtype: "auto"

inference:
  max_new_tokens: 2048
  temperature: 0.7
  top_p: 0.9
```

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡

如有問題，請透過 GitHub Issues 聯絡我們。
