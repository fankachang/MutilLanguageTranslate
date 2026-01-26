# ============================================================
# 多國語言翻譯系統 - 容器映像檔建構腳本 (Windows PowerShell)
# 功能：建構映像檔並自動清理舊的 dangling images
# ============================================================

param(
    [switch]$NoPrune,      # 跳過清理步驟
    [switch]$PruneContainers, # 同時清理停止中的容器（可協助移除仍被引用的舊 image）
    [switch]$Force,        # 強制重新建構（不使用快取）
    [string]$Tag = "latest" # 映像檔標籤
)

$ErrorActionPreference = "Stop"

# 設定顏色輸出
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[SUCCESS] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[WARNING] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }

# 取得專案根目錄
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# 若專案有 .venv 的 podman-compose，優先讓 podman compose 使用它（避免使用系統 Python 安裝的 provider）
$VenvProvider = Join-Path $ProjectRoot ".venv\Scripts\podman-compose.exe"
if (Test-Path $VenvProvider) {
    $env:PODMAN_COMPOSE_PROVIDER = (Resolve-Path $VenvProvider).Path
    Write-Info "已設定 PODMAN_COMPOSE_PROVIDER=$env:PODMAN_COMPOSE_PROVIDER"
}

Write-Info "開始建構容器映像檔..."
Write-Info "專案目錄: $ProjectRoot"
Write-Info "映像檔標籤: $Tag"

# 建構參數
$BuildArgs = @("compose", "build")
if ($Force) {
    $BuildArgs += "--no-cache"
    Write-Info "使用 --no-cache 強制重新建構"
}

# 執行建構
try {
    Write-Info "執行 podman compose build..."
    & podman $BuildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "建構失敗，退出碼: $LASTEXITCODE"
    }
    Write-Success "映像檔建構完成！"
} catch {
    Write-Error "建構過程發生錯誤: $_"
    exit 1
}

# 清理 dangling images
if (-not $NoPrune) {
    Write-Info "清理 dangling images（孤立映像檔）..."

    if ($PruneContainers) {
        Write-Warning "將清理停止中的容器（podman container prune -f）..."
        podman container prune -f
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "清理停止容器時發生問題，仍會繼續嘗試清理 images"
        }
    }

    # 取得清理前的 dangling images 數量
    $DanglingBefore = (podman images -f "dangling=true" -q | Measure-Object).Count

    if ($DanglingBefore -gt 0) {
        Write-Info "發現 $DanglingBefore 個 dangling images，正在清理..."
        podman image prune -f

        if ($LASTEXITCODE -eq 0) {
            Write-Success "已清理 $DanglingBefore 個 dangling images"
        } else {
            Write-Warning "清理過程可能有部分失敗"
        }
    } else {
        Write-Info "沒有 dangling images 需要清理"
    }

    $DanglingAfter = (podman images -f "dangling=true" -q | Measure-Object).Count
    if ($DanglingAfter -gt 0) {
        Write-Warning "清理後仍有 $DanglingAfter 個 dangling images。可能仍被容器引用（包含停止狀態）。"
        Write-Warning "可先執行：podman ps -a  檢查引用，再用：podman container prune -f  或改用本腳本的 -PruneContainers 參數。"
    }
} else {
    Write-Warning "跳過清理步驟（使用了 -NoPrune 參數）"
}

# 顯示目前的映像檔列表
Write-Info "目前的映像檔列表："
podman images --filter "reference=*mutillangtranslate*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.Created}}"

Write-Success "建構流程完成！"
