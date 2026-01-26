# 使用 Python 3.11 作為基礎映像
FROM python:3.11-slim

# 設定標籤
LABEL maintainer="dev@example.com"
LABEL description="多國語言翻譯系統 - TAIDE-LX-7B"
LABEL version="1.0.0"

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Taipei \
    # Django 設定
    DJANGO_SETTINGS_MODULE=translation_project.settings \
    DJANGO_DEBUG=False \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
    # 應用程式設定
    APP_HOME=/app \
    MODEL_PATH=/app/models

# 設定工作目錄
WORKDIR ${APP_HOME}

# 安裝系統相依套件
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 複製 requirements.txt 並安裝 Python 相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式程式碼
COPY config/ ./config/
COPY translation_project/ ./translation_project/

# 切換到 Django 專案目錄（避免 import 路徑錯誤）
WORKDIR ${APP_HOME}/translation_project

# 建立必要目錄
RUN mkdir -p ${MODEL_PATH} \
    && mkdir -p ${APP_HOME}/logs \
    && mkdir -p ./staticfiles

# 收集靜態檔案
RUN python manage.py collectstatic --noinput

# 建立非 root 使用者
RUN groupadd -r translator \
    && useradd -r -g translator translator \
    && chown -R translator:translator ${APP_HOME}

# 切換到非 root 使用者
USER translator

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# 暴露連接埠
EXPOSE 8000

# 設定模型掛載點（使用 volume）
VOLUME ["${MODEL_PATH}"]

# 啟動命令
# 使用 uvicorn 作為 ASGI 伺服器
CMD ["python", "-m", "uvicorn", \
    "translation_project.asgi:application", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
    "--lifespan", "off"]
