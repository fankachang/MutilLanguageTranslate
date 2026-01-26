#!/bin/bash
# ============================================================
# 多國語言翻譯系統 - 容器映像檔建構腳本 (Linux/Mac)
# 功能：建構映像檔並自動清理舊的 dangling images
# ============================================================

set -e

# 預設值
NO_PRUNE=false
PRUNE_CONTAINERS=false
FORCE=false
TAG="latest"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 輸出函數
info() { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# 使用說明
usage() {
    echo "用法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -n, --no-prune    跳過清理步驟"
    echo "  -p, --prune-containers  同時清理停止中的容器（可協助移除仍被引用的舊 image）"
    echo "  -f, --force       強制重新建構（不使用快取）"
    echo "  -t, --tag TAG     映像檔標籤（預設: latest）"
    echo "  -h, --help        顯示此說明"
    exit 0
}

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--no-prune)
            NO_PRUNE=true
            shift
            ;;
        -p|--prune-containers)
            PRUNE_CONTAINERS=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "未知參數: $1"
            usage
            ;;
    esac
done

# 取得專案根目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 若專案有 .venv 的 podman-compose，優先讓 podman compose 使用它（避免依賴系統 Python）
if [ -x "$PROJECT_ROOT/.venv/bin/podman-compose" ]; then
    export PODMAN_COMPOSE_PROVIDER="$PROJECT_ROOT/.venv/bin/podman-compose"
    info "已設定 PODMAN_COMPOSE_PROVIDER=$PODMAN_COMPOSE_PROVIDER"
fi

info "開始建構容器映像檔..."
info "專案目錄: $PROJECT_ROOT"
info "映像檔標籤: $TAG"

# 判斷使用 docker 還是 podman
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    error "找不到 docker 或 podman，請先安裝容器執行環境"
    exit 1
fi

info "使用容器工具: $CONTAINER_CMD"

# 建構參數
BUILD_ARGS="compose build"
if [ "$FORCE" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
    info "使用 --no-cache 強制重新建構"
fi

# 執行建構
info "執行 $CONTAINER_CMD compose build..."
if $CONTAINER_CMD $BUILD_ARGS; then
    success "映像檔建構完成！"
else
    error "建構失敗"
    exit 1
fi

# 清理 dangling images
if [ "$NO_PRUNE" = false ]; then
    info "清理 dangling images（孤立映像檔）..."

    if [ "$PRUNE_CONTAINERS" = true ]; then
        warning "將清理停止中的容器（$CONTAINER_CMD container prune -f）..."
        $CONTAINER_CMD container prune -f || warning "清理停止容器時發生問題，仍會繼續嘗試清理 images"
    fi

    # 取得清理前的 dangling images 數量
    DANGLING_COUNT=$($CONTAINER_CMD images -f "dangling=true" -q | wc -l)

    if [ "$DANGLING_COUNT" -gt 0 ]; then
        info "發現 $DANGLING_COUNT 個 dangling images，正在清理..."
        $CONTAINER_CMD image prune -f
        success "已清理 $DANGLING_COUNT 個 dangling images"
    else
        info "沒有 dangling images 需要清理"
    fi

    DANGLING_AFTER=$($CONTAINER_CMD images -f "dangling=true" -q | wc -l)
    if [ "$DANGLING_AFTER" -gt 0 ]; then
        warning "清理後仍有 $DANGLING_AFTER 個 dangling images。可能仍被容器引用（包含停止狀態）。"
        warning "可先用：$CONTAINER_CMD ps -a  檢查引用，再用：$CONTAINER_CMD container prune -f  或加上 --prune-containers 參數。"
    fi
else
    warning "跳過清理步驟（使用了 --no-prune 參數）"
fi

# 顯示目前的映像檔列表
info "目前的映像檔列表："
$CONTAINER_CMD images --filter "reference=*mutillangtranslate*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.Created}}"

success "建構流程完成！"
