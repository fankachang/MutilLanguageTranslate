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

        # 在開發模式下，Django 會啟動兩個進程（reloader 與 main）
        # 檢查是否使用 --noreload
        use_noreload = '--noreload' in sys.argv
        is_main_process = os.environ.get('RUN_MAIN') == 'true'

        # 如果有 reloader 且不是 main 進程，則跳過
        if not use_noreload and not is_main_process:
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
                        logger.info(
                            f"✓ 執行模式: {model_service.get_execution_mode()}")
                        logger.info("=" * 60)
                    else:
                        logger.error("=" * 60)
                        logger.error(
                            f"✗ 翻譯模型載入失敗: {model_service.get_error_message()}")
                        logger.error("=" * 60)

                # 啟動背景執行緒
                load_thread = threading.Thread(
                    target=load_model_async, daemon=True)
                load_thread.start()
                logger.info("✓ 背景載入執行緒已啟動，Django 服務即將就緒")

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"✗ 模型載入過程中發生錯誤: {e}", exc_info=True)
            logger.error("=" * 60)
