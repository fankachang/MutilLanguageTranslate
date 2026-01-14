# TAIDE-LX-7B-Chat 驗證指南

## ⚠️ 當前問題

您的系統在載入 TAIDE-LX-7B-Chat 模型時遇到問題：

1. **記憶體不足**：8GB VRAM 不足以載入完整的 7B float16 模型（需要約 14GB）
2. **bitsandbytes 不相容**：Windows 上的 4-bit 量化支援有問題
3. **CPU 載入緩慢**：CPU 模式記憶體需求約 28GB RAM

## 💡 解決方案

### 選項 1: 安裝 Windows 相容的 bitsandbytes

```powershell
# 安裝 Windows 版本的 bitsandbytes
pip install https://github.com/jllllll/bitsandbytes-windows-webui/releases/download/wheels/bitsandbytes-0.41.1-py3-none-win_amd64.whl
```

然後修改配置啟用 4-bit：
```yaml
# config/model_config.yaml
quantization:
  enable_4bit: true
  load_in_4bit: true
```

### 選項 2: 使用 OpenAI 相容 API（推薦）

將模型部署到獨立的推論服務（如 vLLM、Ollama），然後修改配置：

```yaml
# config/model_config.yaml
provider:
  type: "openai"  # 改為 openai

  openai:
    api_base: "http://localhost:8000/v1"
    api_key: null
    model: "TAIDE-LX-7B-Chat"
    timeout: 120
    max_retries: 2
```

**部署 vLLM 範例**（需要 Linux 或 WSL）：
```bash
# 安裝 vLLM
pip install vllm

# 啟動 vLLM 服務
python -m vllm.entrypoints.openai.api_server \
    --model /path/to/TAIDE-LX-7B-Chat \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --dtype float16
```

### 選項 3: 跳過模型載入，僅驗證 API 結構

暫時跳過模型載入以測試其他功能：

```powershell
# 設定環境變數
$env:SKIP_MODEL_LOAD = "true"

# 啟動服務
cd translation_project
..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --noreload
```

## 🧪 驗證指令

### 1. 檢查服務健康狀態
```powershell
curl http://localhost:8000/api/health/
```

### 2. 查看支援的語言
```powershell
curl http://localhost:8000/api/languages/
```

### 3. 測試翻譯 API（需要模型已載入）
```powershell
# 建立測試請求檔案
@"
{
    "text": "Hello, how are you?",
    "source_language": "en",
    "target_language": "zh-TW",
    "quality_mode": "standard"
}
"@ | Out-File -Encoding utf8 test_request.json

# 發送請求
curl -X POST http://localhost:8000/api/translate/ `
  -H "Content-Type: application/json" `
  -d "@test_request.json"
```

### 4. 在瀏覽器中測試
- 開啟：http://localhost:8000/
- 前端界面：http://localhost:8000/translator/

## 📊 Prompt 格式驗證

即使模型未載入，您仍可透過測試腳本驗證 Prompt 格式：

```powershell
..\.venv\Scripts\python.exe test_taide_chat.py
```

所有測試應該通過，確認：
- ✅ 模型配置已更新為 TAIDE-LX-7B-Chat
- ✅ Prompt 格式符合 Llama 2 Chat 規範
- ✅ BOS token 正確添加
- ✅ `[/INST]` 後無多餘提示詞

## 🔧 下一步建議

1. **短期**：使用選項 3 驗證 API 結構和 Prompt 格式
2. **中期**：安裝 Windows 相容的 bitsandbytes（選項 1）
3. **長期**：部署獨立推論服務（選項 2，效能最佳）

需要協助任何步驟請告訴我！
