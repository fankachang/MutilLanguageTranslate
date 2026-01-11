````chatagent
# MutilLangTranslate Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-08

## Active Technologies

### Language & Framework
- **Python 3.11+**: 專案最低版本要求
- **Django 4.2+ (ASGI)**: 全端框架，支援非同步處理
- **PyTorch 2.x + Transformers**: AI 模型推論
- **Django-Q**: 輕量級任務佇列（批量翻譯非同步處理）
- **Django-Ratelimit**: API 限流保護
- **HTMX 1.9+ + Alpine.js 3.x**: 前端輕量級互動框架

### Storage & Data
- **無傳統資料庫**: 避免 PostgreSQL/MySQL 依賴
- **sessionStorage**: 前端暫存翻譯歷史（標籤頁關閉即清除）
- **localStorage**: 使用者偏好設定（永久儲存）
- **SQLite**: 僅用於 Django-Q 任務佇列管理
- **檔案系統**: 日誌檔案、批量翻譯結果暫存

### AI Model
- **TAIDE-LX-7B-Chat**: 本地部署的 AI 翻譯模型
- **CUDA 11.8/12.1**: GPU 加速（可選，自動降級至 CPU）

## Project Structure

```text
MutilLangTranslate/
├── src/                      # 主要原始碼
│   ├── app.py               # Django ASGI 入口
│   ├── models/              # 資料模型與 AI 客戶端
│   ├── services/            # 業務邏輯（翻譯服務）
│   ├── api/                 # API 視圖
│   ├── ui/                  # Django Templates + 靜態檔案
│   └── utils/               # 工具函式
├── tests/                    # 測試套件
│   ├── unit/
│   ├── integration/
│   └── performance/
├── config/                   # YAML 配置檔案
├── models/                   # TAIDE 模型檔案
├── data/                     # 日誌與暫存資料
└── specs/                    # 規格文件
    └── 001-taide-translation/
```

## Development Commands

```bash
# 執行測試
cd src; pytest

# 程式碼檢查
ruff check .

# 啟動開發伺服器
python src/app.py runserver 0.0.0.0:8000

# 啟動 ASGI 伺服器（生產環境）
uvicorn src.app:application --host 0.0.0.0 --port 8000 --workers 4
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

## Recent Changes
- 2026-01-08: Phase 0 & Phase 1 完成（研究、設計、契約）
- 2026-01-08: 技術棧確認（Django + PyTorch + HTMX + Alpine.js）
- 2026-01-08: 更新 plan.md 技術背景與專案結構

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

````
