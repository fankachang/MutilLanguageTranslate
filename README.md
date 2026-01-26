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

| 項目   | 最低需求 | 建議配置                |
| ------ | -------- | ----------------------- |
| CPU    | 4 核心   | 8 核心以上              |
| 記憶體 | 16 GB    | 32 GB 以上              |
| GPU    | -        | NVIDIA GPU (16GB+ VRAM) |
| 磁碟   | 50 GB    | 100 GB SSD              |

### 軟體需求

- Python 3.11（推薦；Windows 上務必使用 3.11 以確保 PyTorch cu118 相容性，但若系統有 3.10 也可以）
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
# 若專案根目錄已存在 .venv/，請不要重建，直接啟用即可。

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 3. 安裝相依套件

#### CPU 模式（或已安裝 PyTorch）

```bash
pip install -r requirements.txt
```

#### GPU 模式（NVIDIA CUDA）

**重要：** 請使用 Python 3.10 或 3.11（PyTorch cu118 wheel 支援這些版本）。

```powershell
# 升級 pip
pip install --upgrade pip

# 1. 安裝 PyTorch with CUDA 11.8
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision

# 2. 安裝專案相依套件
pip install -r requirements.txt

# 3. (可選) 安裝 bitsandbytes 以啟用 4-bit 量化（適用於 8GB VRAM 以下的 GPU）
# Windows 上可能需要 Visual Studio Build Tools
pip install bitsandbytes
```

**疑難排解：**
- 若 Python 版本為 3.14 等較新版本，PyTorch 官方 wheel 可能尚未支援，請使用 `py -3.10` 或 `py -3.11` 建立虛擬環境。
- bitsandbytes 在 Windows 上可能需要編譯工具，若安裝失敗可跳過（系統會自動使用 float16 模式）。

### 4. 設定配置檔

```bash
# 複製範例配置檔

# Linux/macOS/Git Bash
cp config/app_config.yaml.example config/app_config.yaml
cp config/model_config.yaml.example config/model_config.yaml

# Windows PowerShell
Copy-Item config/app_config.yaml.example config/app_config.yaml
Copy-Item config/model_config.yaml.example config/model_config.yaml

# 依據需求編輯配置檔
```

### 5. 下載模型

本專案預設使用 **本機模型**（`provider.type: local`），且預設路徑為 `models/TAIDE-LX-7B-Chat`（見 `config/model_config.yaml`）。

- 若 `models/` 目錄已包含模型資料夾（例如 `models/TAIDE-LX-7B-Chat/`、`models/Llama-3.1-TAIDE-LX-8B-Chat/`），可直接啟動服務。
- 若 `models/` 尚未放置模型，請先把模型下載/放到對應路徑（必須包含 `config.json` 等檔案），否則載入時會因「模型路徑不存在」而失敗。

備註：README 先前提到「首次啟動自動下載」不符合目前預設設定（目前預設是掃描/載入本機目錄）。如需改成遠端/自動下載模式，建議改用 `provider.type: openai`（或自行調整為 Hugging Face 來源）。

### 6. 啟動服務

```bash
cd translation_project

# 開發模式
..\.venv\Scripts\python.exe manage.py runserver

# 生產模式（使用 uvicorn）
uvicorn translation_project.asgi:application --host 0.0.0.0 --port 8000
```

### 7. 開啟瀏覽器

造訪 http://localhost:8000 開始使用翻譯服務。

### 重要：模型載入改為手動啟動

為了避免啟動時就佔用大量資源，服務啟動後**不會自動載入模型**。

- 請開啟 http://localhost:8000/admin/status/
- 在「要啟動的模型」選擇模型後按下「選擇後開始載入」

若你想維持舊行為（啟動就自動載入），可設定環境變數：

```powershell
$env:TRANSLATOR_AUTO_LOAD_MODEL_ON_STARTUP = "1"
```

## GPU 記憶體最佳化（自動偵測）

系統會**自動偵測** GPU 記憶體大小並選擇最佳載入模式：

- **VRAM ≤ 12GB**（例如 RTX 4060 8GB, RTX 3060 12GB）：自動啟用 **4-bit 量化**，節省 70-75% 記憶體
- **VRAM > 12GB**（例如 RTX 4090 24GB）：使用 **float16 模式**，保持最佳品質

無需手動設定，系統會自動選擇最適合的模式。

### 手動視盖自動偵測（可選）

若您想強制使用特定模式，可修改 `config/model_config.yaml`：

```yaml
# 強制啟用 4-bit 量化（忽略自動偵測）
quantization:
  enable_4bit: true
  load_in_4bit: true

# 或強制停用 4-bit 量化（使用 float16）
quantization:
  enable_4bit: false
```

### bitsandbytes 安裝說明

4-bit 量化需要 `bitsandbytes` 套件（已包含在 `requirements.txt` 中）：

- **Linux**: 直接安裝即可
- **Windows**: 可能需要 [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)（C++ 開發工具）

若 bitsandbytes 安裝失敗或不可用，系統會自動退回使用 float16 模式。

### 方法 2：CPU/GPU Offload（accelerate）

使用 `accelerate` 將模型部分層移至 CPU 或磁碟，以適配 GPU 記憶體限制。

```powershell
# accelerate 已在 requirements.txt 中，確認已安裝
pip install accelerate
```

`config/model_config.yaml` 中設定 `max_gpu_memory` 為您的 VRAM 大小：

```yaml
model:
  max_gpu_memory: 8  # 8GB VRAM
```

系統會自動使用 `device_map="auto"` 將模型層分配到 GPU/CPU/磁碟。

### 測試設定

您可以使用內建的測試 API 驗證設定是否正確：

```powershell
# 測試載入小模型（gpt2）以驗證 GPU 與量化設定
curl -X POST http://localhost:8000/api/v1/admin/model/test/ -H "Content-Type: application/json" -d '{"model_name": "gpt2"}'
```

或使用我們提供的測試腳本：

```powershell
.venv\Scripts\python tests\quick_model_test.py
```

## 容器部署（Podman / Docker / Compose）

> 驗證重點：服務啟動後 `GET /api/health/` 需回 200。

### Windows 使用 Podman 的前置（必要）

Podman 在 Windows 上需要透過 VM（預設為 WSL）執行 Linux containers，因此第一次使用前請先把 Podman 的 machine 啟起來：

```powershell
# 第一次使用（會建立 VM）
podman machine init --now

# 之後要啟動/停止 VM
podman machine start
podman machine stop

# 檢查狀態
podman machine list
podman info
```

建議安裝 Podman Desktop 來管理 machine/映像/容器（可選，但對 Windows 方便）。

### 使用 Podman

```bash
# 建置映像
podman build -t translation-service -f Containerfile .

# 執行容器
podman run -d \
  --name translation-service \
  -p 8000:8000 \
  -v ./models:/app/models:ro \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  translation-service
```

### 使用 Podman Compose（推薦，直接沿用 docker-compose.yaml）

本專案已提供 `docker-compose.yaml`，Podman 可以用 `podman compose` 直接啟動：

```bash
podman compose -f docker-compose.yaml up -d
```

停止並清掉容器/網路：

```bash
podman compose -f docker-compose.yaml down
```

注意：`podman compose` 會呼叫外部 compose provider（例如 `docker-compose` 或 `podman-compose`）。
若你執行 `podman compose` 時提示找不到 provider，請先安裝其中一個：

```powershell
# 建議：安裝到本專案的 .venv，避免使用系統 Python
.\.venv\Scripts\python.exe -m pip install podman-compose

# (可選，但推薦) 指定 podman compose 要使用 .venv 裡的 provider
$env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path .\.venv\Scripts\podman-compose.exe).Path
```

或是直接用 `.venv` 內的 `podman-compose`（完全不依賴系統 Python）：

```powershell
.\.venv\Scripts\podman-compose.exe -f docker-compose.yaml up -d
```

### 使用 Docker

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

### 使用 Docker Compose

```bash
docker compose -f docker-compose.yaml up -d
```

#### GPU 注意事項（Docker / Podman）

- `docker-compose.yaml` 目前以 **CDI**（`nvidia.com/gpu=all`）的方式宣告 GPU。
- 若你使用 Docker，需先安裝並正確設定 NVIDIA Container Toolkit（並啟用 CDI 或使用等效的 GPU 掛載方式），否則容器雖可啟動但無法使用 GPU。
- 若你使用 Podman Desktop / Podman machine，請確認 VM 具備 GPU passthrough 與對應驅動支援。

##### NVIDIA Container Toolkit（Linux）快速安裝/驗證（建議）

> 不同發行版/版本安裝方式略有差異；以下以常見 Linux 發行版為例。若你不是在 Linux 上跑容器（例如 Windows 的 Docker Desktop / Podman machine），請以該平台的 GPU/WSL2 指南為準。

1) **先確認主機端 NVIDIA 驅動可用**

```bash
nvidia-smi
```

2) **安裝 NVIDIA Container Toolkit**（參考官方文件）

- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

3) **啟用/生成 CDI 設定**（讓 `nvidia.com/gpu=all` 可用）

```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

4) **重啟容器引擎**

- Docker：`sudo systemctl restart docker`
- Podman：若使用 `podman`（rootless/rootful）與環境不同，請依你的服務管理方式重啟對應 daemon / machine

5) **驗證 GPU 容器可用**

```bash
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

##### Podman（Linux）完整步驟：安裝 NVIDIA Container Toolkit + CDI

> 這份流程適用於「Podman 直接跑在 Linux 主機」的情境（不是 Windows 的 podman machine）。

0) **確認主機已安裝 NVIDIA 驅動**

```bash
nvidia-smi
```

1) **安裝 nvidia-container-toolkit**

- **Ubuntu / Debian**（建議依官方文件操作，會自動加 repo 與 key）

  - 官方安裝指南：
    - https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

- **Fedora / RHEL / Rocky / Alma**

  - 同上官方安裝指南（依你的發行版選擇對應章節）

2) **生成 CDI 設定（讓 Podman 可用 `--device nvidia.com/gpu=all`）**

```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

3) **重新啟動 / 重新進入 Podman session（視環境而定）**

```bash
podman info | head
```

4) **用 Podman 驗證 GPU 真的可用**

```bash
podman run --rm --device nvidia.com/gpu=all \
  nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

若你看到 GPU 資訊輸出（driver 版本、GPU 名稱），代表 nvidia-container-toolkit + CDI 已就緒。

5) **接著再用本專案 compose 啟動**

```bash
podman compose -f docker-compose.yaml up -d
```

##### Podman machine（Windows / WSL2）注意事項

- 需要先確保 **Windows 主機**已安裝支援 WSL2 GPU 的 NVIDIA 驅動，且在 WSL2 裡能跑 `nvidia-smi`。
- `nvidia-container-toolkit` 也必須**安裝在 VM/WSL2 的 Linux 內**（不是裝在 Windows 本機），並在 Linux 內執行 `nvidia-ctk cdi generate`。
- 若你的 podman machine 沒有 GPU passthrough 能力（常見），即使工具裝好也不一定能在 VM 內看到 GPU；此時建議改用「在 WSL2 內直接跑 Podman」或改用 Docker Desktop（若你的目標是 GPU 容器）。

##### Windows（WSL2）+ podman machine：在 machine 內安裝（你目前預期的方式）

> **能不能用 GPU，取決於 GPU 是否能被 podman machine 看到。**
> 很多 Windows 的 podman machine 情境下，GPU 不一定能 passthrough 到 machine 內的 Linux VM。

1) **先確認 Windows/WSL2 的 GPU 驅動就緒**

- 確保已安裝「支援 WSL2」的 NVIDIA 驅動（建議用最新 Studio/Game Ready Driver）。
- 在任一個 WSL2 發行版內驗證（如果你沒有 WSL2 發行版，可先安裝 Ubuntu）：

```bash
nvidia-smi
```

若這一步就失敗，請先把 WSL2 的 GPU 環境修好；否則後面在 podman machine 內也不會成功。

2) **啟動並進入 podman machine**

```powershell
podman machine start
podman machine ssh
```

3) **在 machine 內確認 GPU 裝置是否存在**

在 machine 的 shell 內執行：

```bash
ls -l /dev/nvidia* 2>/dev/null || true
ls -l /dev/dxg 2>/dev/null || true
```

- 若完全看不到任何 NVIDIA 相關裝置，代表 GPU 目前沒有 passthrough 到 machine：這種情況下，安裝 toolkit 也無法讓 GPU magically 出現。
- 若能看到裝置，才建議繼續往下做。

4) **辨識 machine 的 Linux 類型（決定用哪個套件管理器）**

```bash
cat /etc/os-release
command -v apt-get || true
command -v dnf || true
command -v rpm-ostree || true
```

5) **安裝 nvidia-container-toolkit（依發行版）**

- **Ubuntu（apt；含 WSL2 podman machine 常見情境）**：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

- 若 machine 內有 `dnf`（Fedora/RHEL 類）：

```bash
sudo dnf install -y ca-certificates curl
sudo curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo \
  -o /etc/yum.repos.d/nvidia-container-toolkit.repo
sudo dnf install -y nvidia-container-toolkit
```

- 若 machine 內只有 `rpm-ostree`（例如 CoreOS/不可變系統）：

  - 這類系統「不一定」適合/支援直接用上述方式安裝。
  - 建議改走「在 WSL2 發行版內直接安裝 Podman」的路徑（見下方替代方案）。

6) **生成 CDI 設定**

```bash
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
```

（建議）若是在 **podman machine** 內操作，生成 CDI 後可以退出並重啟 machine，確保 device 設定被重新載入：

```powershell
exit
podman machine stop
podman machine start
podman machine ssh
```

7) **在 machine 內用 Podman 驗證**

```bash
podman run --rm --device nvidia.com/gpu=all \
  nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

若你在這一步遇到權限/SELinux 相關錯誤，可嘗試：

- 改用 rootful：`sudo podman run ...`
- 或暫時加上：`--security-opt=label=disable`

8) **再回到 Windows 端啟動 compose**

```powershell
podman compose -f docker-compose.yaml up -d
```

##### 替代方案（通常更穩）：在 WSL2 發行版內直接跑 Podman（不使用 podman machine）

如果你的 podman machine 無法看到 GPU，最常見的可行做法是：

1) 在 WSL2（Ubuntu）內安裝 Podman
2) 在同一個 WSL2 內安裝 `nvidia-container-toolkit` 並生成 CDI
3) 直接在該 WSL2 內執行 `podman run --device nvidia.com/gpu=all ...`

這樣容器跑在 WSL2 distro 內，比較容易吃到 WSL2 的 GPU 支援。

##### Linux（Ubuntu）原生 Podman：Ubuntu（apt）安裝命令

若是在「Ubuntu Linux 主機」直接跑 Podman（不是 Windows podman machine），安裝 toolkit 也可用同一套 apt 指令：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml

podman run --rm --device nvidia.com/gpu=all \
  nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

##### 若 CDI 尚未就緒怎麼辦？

- 若短期內只想先跑起來且不想處理 CDI，也可以改用 Docker 的 `--gpus all`（但這需要調整 compose 或改用 `docker run`）。
- 本專案 compose 目前使用 CDI 宣告；若你希望我幫你補一份「Docker 非 CDI」版本的 compose（例如 `deploy.resources.reservations.devices` 或 runtime 設定），告訴我你的 Docker 版本與 OS，我可以直接加檔。

### 健康檢查

```bash
curl -f http://localhost:8000/api/health/
```

## 目錄結構

```
MutilLanguageTranslate/
├── config/                          # 配置檔目錄
│   ├── app_config.yaml              # 應用程式配置
│   ├── model_config.yaml            # 模型配置
│   └── languages.yaml               # 語言定義
├── logs/                            # 日誌目錄
├── models/                          # 模型目錄
│   ├── TAIDE-LX-7B-Chat/            # 模型名稱一（建議使用，請自行下載）
│   └── Llama-3.1-TAIDE-LX-8B-Chat/  # 模型名稱二（建議使用，請自行下載）
├── translation_project/             # Django 專案
│   ├── translation_project/         # 專案設定
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── asgi.py
│   └── translator/                  # 翻譯應用程式
│       ├── api/                     # REST API
│       ├── services/                # 服務層
│       ├── templates/               # 前端模板
│       ├── static/                  # 靜態資源
│       └── utils/                   # 工具函數
├── specs/                           # 規格文件
├── tests/                           # 測試
├── Containerfile                    # 容器建置檔
├── docker-compose.yaml              # Docker Compose
├── requirements.txt                 # Python 相依套件
└── README.md                        # 本文件
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

### 管理 API

#### POST /api/v1/admin/model/test/

測試載入小型模型（用於驗證環境與量化設定）。

**請求**
```json
{
  "model_name": "gpt2"
}
```

**回應**
```json
{
  "success": true,
  "message": "小模型載入與推論成功 (gpt2)",
  "model_info": {
    "model_name": "gpt2",
    "generated": "Hello world, I'm not sure what to say",
    "cuda_available": true,
    "cuda_device_count": 1
  }
}
```

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

## 界面範例

![](./Docs/images/Interfase.png)
![](./Docs/images/History.png)
![](./Docs/images/Setting.png)

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡

如有問題，請透過 GitHub Issues 聯絡我們。
