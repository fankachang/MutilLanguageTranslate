````chatagent
# MutilLangTranslate Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-11

## Active Technologies

### Language & Framework
- **Python 3.11+**: 專案最低版本要求
- **Django 4.2+ (ASGI)**: 全端框架，支援非同步處理
- **PyTorch 2.x + Transformers**: AI 模型推論
- **HTMX 1.9+ + Alpine.js 3.x**: 前端輕量級互動框架
- **uvicorn**: ASGI 伺服器

### Storage & Data
- **無傳統資料庫**: 避免 PostgreSQL/MySQL 依賴
- **Django Cache Framework**: 記憶體內快取（翻譯佇列、系統狀態）
- **sessionStorage**: 前端暫存翻譯歷史（標籤頁關閉即清除）
- **localStorage**: 使用者偏好設定（永久儲存）
- **檔案系統**: 日誌檔案儲存

### AI Model
- **TAIDE-LX-7B**: 本地部署的 AI 翻譯模型
- **模型路徑**: `models/models--taide--TAIDE-LX-7B/snapshots/099c425ede93588d7df6e5279bd6b03f1371c979`
- **CUDA 12.0+**: GPU 加速（可選，自動降級至 CPU）

### Containerization
- **Podman 4.0+**: 容器引擎（Docker 相容替代）
- **Containerfile**: 使用 Containerfile 而非 Dockerfile（兩者語法相容）
- **GPU 支援**: 需安裝 nvidia-container-toolkit

## Project Structure

```text
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
│       ├── api/                  # REST API 視圖
│       ├── services/             # 業務邏輯（翻譯服務）
│       ├── middleware/           # 中介軟體（IP 白名單）
│       ├── templates/            # Django Templates
│       └── static/               # 靜態檔案（HTMX, Alpine.js）
│
├── config/                       # YAML 配置檔案
│   ├── app_config.yaml
│   ├── model_config.yaml
│   └── languages.yaml
│
├── logs/                         # 日誌目錄
├── models/                       # TAIDE 模型檔案
├── tests/                        # 測試套件
│   ├── unit/
│   ├── integration/
│   └── performance/
│
└── specs/                        # 規格文件
    └── 001-multilang-translation/
```

## Development Commands

```bash
# 建立虛擬環境
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt

# 執行測試
pytest

# 程式碼檢查
ruff check .

# 啟動開發伺服器（熱重載）
cd translation_project
uvicorn translation_project.asgi:application --reload --port 8000

# 啟動 ASGI 伺服器（生產環境）
uvicorn translation_project.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

## Code Style

- **語言**: Python 3.11+
- **風格指南**: 遵循 PEP 8
- **類型提示**: 推薦使用（提升程式碼可讀性）
- **註解**: 必須使用繁體中文（zh-TW）
- **Commit 訊息**: 遵循 Conventional Commits，使用繁體中文

## Key Constraints

1. **完全離線運行**: 內網環境，無外部 API 呼叫
2. **效能目標**: GPU 模式 2-3 秒，CPU 模式 8-10 秒（1000 字翻譯）
3. **並發支援**: 100 並發使用者，佇列上限 100
4. **簡單優先**: 遵循 YAGNI 原則，避免過度工程
5. **測試驅動**: 所有業務邏輯需有單元測試
6. **IP 白名單**: 管理端點需限制內部 IP 存取

## API Endpoints

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/translate/` | POST | 執行翻譯 |
| `/api/v1/translate/{id}/status/` | GET | 查詢翻譯狀態 |
| `/api/v1/languages/` | GET | 取得支援語言清單 |
| `/api/v1/admin/status/` | GET | 系統狀態（需 IP 白名單） |
| `/api/v1/admin/statistics/` | GET | 統計資料（需 IP 白名單） |
| `/api/health/` | GET | 健康檢查 |

## Recent Changes
- 2026-01-11: 技術棧遷移至 Django 4.2+，移除 .NET 相關配置
- 2026-01-11: Phase 0 & Phase 1 完成（研究、設計、契約）

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

````
