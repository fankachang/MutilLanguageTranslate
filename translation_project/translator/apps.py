import threading
import logging
from django.apps import AppConfig


class TranslatorConfig(AppConfig):
    name = 'translator'

    def ready(self):
        """
        Django 應用準備就緒時執行初始化
        同步載入翻譯模型，顯示完整載入進度
        """
        import os
        import sys
        logger = logging.getLogger('translator')

        # 只在「真的要啟動 Web 服務」時才載入模型。
        # 避免在 build 階段（collectstatic）、migrate、測試等管理指令時不必要地載入大型模型。
        argv_lower = " ".join(sys.argv).lower()
        is_runserver = 'runserver' in sys.argv
        is_uvicorn = 'uvicorn' in argv_lower

        if not (is_runserver or is_uvicorn):
            return

        # Django runserver 在開發模式下會有 reloader 與 main 兩個進程。
        # 只有 runserver 才需要 RUN_MAIN 判斷；uvicorn/容器啟動不會設定 RUN_MAIN。
        use_noreload = '--noreload' in sys.argv
        is_main_process = os.environ.get('RUN_MAIN') == 'true'

        if is_runserver and (not use_noreload) and (not is_main_process):
            logger.info("跳過 reloader 進程的模型載入")
            return

        try:
            from translator.services.model_service import get_model_service

            model_service = get_model_service()

            if not model_service.is_loaded():
                logger.info("=" * 60)
                logger.info("Django 啟動完成，將在背景載入翻譯模型...")
                logger.info("=" * 60)

                # 使用執行緒在背景載入模型，避免阻塞 Django 啟動
                def load_model_async():
                    logger.info("開始背景載入模型...")
                    success = model_service.load_model()

                    if success:
                        logger.info("=" * 60)
                        logger.info("✓ 翻譯模型載入完成，系統已就緒")
                        logger.info("✓ 執行模式: %s", model_service.get_execution_mode())
                        logger.info("=" * 60)
                    else:
                        logger.error("=" * 60)
                        logger.error(
                            "✗ 翻譯模型載入失敗: %s",
                            model_service.get_error_message(),
                        )
                        logger.error("=" * 60)

                # 啟動背景執行緒
                load_thread = threading.Thread(
                    target=load_model_async, daemon=True)
                load_thread.start()
                logger.info("✓ 背景載入執行緒已啟動，Django 服務即將就緒")

        except Exception as e:
            logger.error("=" * 60)
            logger.error("✗ 模型載入過程中發生錯誤: %s", e, exc_info=True)
            logger.error("=" * 60)
