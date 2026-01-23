"""
多國語言翻譯系統 - API 視圖

定義所有 REST API 端點的視圖函數
"""

import json
import logging
from uuid import UUID

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from translator.enums import QualityMode, TranslationStatus
from translator.errors import ErrorCode, TranslationError, get_error_message, get_http_status
from translator.models import TranslationRequest
from translator.services.queue_service import get_queue_service
from translator.services.translation_service import get_translation_service
from translator.services.model_catalog_service import ModelCatalogService
from translator.services.model_service import ModelService
from translator.utils.config_loader import ConfigLoader
from translator.utils.model_id import validate_model_id

logger = logging.getLogger('translator')


def get_client_ip(request: HttpRequest) -> str:
    """取得客戶端 IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_exempt
@require_http_methods(["POST"])
def translate(request: HttpRequest) -> JsonResponse:
    """
    POST /api/v1/translate/

    執行文字翻譯
    """
    try:
        # 解析請求
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': '無效的 JSON 格式',
                    }
                },
                status=400
            )

        # 取得請求參數
        text = data.get('text', '')
        source_language = data.get('source_language', 'auto')
        target_language = data.get('target_language')
        quality = data.get('quality', QualityMode.STANDARD)
        model_id = data.get('model_id')

        # 驗證必要參數
        if not target_language:
            return JsonResponse(
                {
                    'error': {
                        'code': ErrorCode.VALIDATION_INVALID_LANGUAGE,
                        'message': '缺少目標語言參數',
                    }
                },
                status=400
            )

        # 驗證品質參數
        if not QualityMode.is_valid(quality):
            quality = QualityMode.STANDARD

        # 可選：驗證 model_id（保持向後相容：未提供則沿用既有行為）
        if model_id is not None:
            model_id = validate_model_id(model_id)
            available = {m.model_id for m in ModelCatalogService.list_models()}
            if model_id not in available:
                raise TranslationError(ErrorCode.MODEL_NOT_FOUND)

            # 若使用者指定 model_id，且與目前 active model 不同：
            # - policy=lazy：嘗試自動切換
            # - policy=explicit：要求先呼叫切換 API
            active_model_id = ModelService.get_active_model_id()
            if active_model_id is not None and active_model_id != model_id:
                model_config = ConfigLoader.get_model_config()
                policy = (
                    model_config.get('models', {})
                    .get('switching', {})
                    .get('policy', 'explicit')
                )

                if policy == 'lazy':
                    ModelService.switch_model(model_id=model_id, force=False)
                else:
                    raise TranslationError(
                        ErrorCode.MODEL_SWITCH_REJECTED,
                        '目前模型尚未切換完成，請先切換模型後再翻譯',
                    )

        # 建立翻譯請求
        translation_request = TranslationRequest(
            text=text,
            source_language=source_language,
            target_language=target_language,
            quality=quality,
            model_id=model_id,
            client_ip=get_client_ip(request),
        )

        # 執行翻譯
        service = get_translation_service()
        response = service.translate(translation_request)

        # 建立回應
        result = {
            'request_id': response.request_id,
            'status': response.status,
        }

        # 根據狀態添加不同的欄位
        if response.status == TranslationStatus.COMPLETED:
            result['translated_text'] = response.translated_text
            result['processing_time_ms'] = response.processing_time_ms
            result['execution_mode'] = response.execution_mode

            if response.detected_language:
                result['detected_language'] = response.detected_language
            if response.confidence_score is not None:
                result['confidence_score'] = response.confidence_score

            return JsonResponse(result, status=200)

        elif response.status == TranslationStatus.PENDING:
            # 排隊中
            queue_service = get_queue_service()
            queue_status = queue_service.get_status(response.request_id)

            result['queue_position'] = queue_status.get('queue_position', 0)
            result['estimated_wait_seconds'] = result['queue_position'] * 3

            return JsonResponse(result, status=202)

        elif response.status == TranslationStatus.FAILED:
            result['error'] = {
                'code': response.error_code,
                'message': response.error_message,
            }

            http_status = get_http_status(response.error_code)
            return JsonResponse(result, status=http_status)

        else:
            return JsonResponse(result, status=200)

    except TranslationError as e:
        return JsonResponse(
            {
                'error': {
                    'code': e.code,
                    'message': e.message,
                }
            },
            status=e.http_status
        )
    except Exception as e:
        logger.error(f"翻譯 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def translate_status(request: HttpRequest, request_id: UUID) -> JsonResponse:
    """
    GET /api/v1/translate/{request_id}/status/

    查詢翻譯請求狀態
    """
    try:
        queue_service = get_queue_service()
        status = queue_service.get_status(str(request_id))

        if status is None:
            return JsonResponse(
                {
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': '找不到該請求',
                    }
                },
                status=404
            )

        return JsonResponse(status, status=200)

    except Exception as e:
        logger.error(f"查詢狀態 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def languages(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/languages/

    取得支援的語言清單
    """
    try:
        enabled_languages = ConfigLoader.get_enabled_languages()

        return JsonResponse({
            'languages': [lang.to_dict() for lang in enabled_languages],
            'default_source_language': ConfigLoader.get_default_source_language(),
            'default_target_language': ConfigLoader.get_default_target_language(),
        })

    except Exception as e:
        logger.error(f"語言 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def models_list(request: HttpRequest) -> JsonResponse:
    """GET /api/v1/models/ - 取得可用模型清單"""
    try:
        models = ModelCatalogService.list_models()
        selected_model_id = request.session.get("selected_model_id")
        active_model_id = ModelService.get_active_model_id()

        return JsonResponse(
            {
                "models": [
                    {
                        "model_id": m.model_id,
                        "display_name": m.display_name,
                        "has_config": m.has_config,
                        "last_error_message": m.last_error_message,
                    }
                    for m in models
                ],
                "active_model_id": active_model_id,
                "selected_model_id": selected_model_id,
            },
            status=200,
        )

    except Exception as e:
        logger.error(f"models_list 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500,
        )


@csrf_exempt
@require_http_methods(["PUT"])
def models_selection(request: HttpRequest) -> JsonResponse:
    """PUT /api/v1/models/selection/ - 設定本會話選定模型"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': '無效的 JSON 格式',
                    }
                },
                status=400,
            )

        model_id = validate_model_id(data.get("model_id"))

        available = {m.model_id for m in ModelCatalogService.list_models()}
        if model_id not in available:
            raise TranslationError(ErrorCode.MODEL_NOT_FOUND)

        request.session["selected_model_id"] = model_id
        active_model_id = ModelService.get_active_model_id()

        return JsonResponse(
            {
                "selected_model_id": model_id,
                "active_model_id": active_model_id,
                "requires_switch": active_model_id != model_id,
            },
            status=200,
        )

    except TranslationError as e:
        return JsonResponse(
            {
                'error': {
                    'code': e.code,
                    'message': e.message,
                }
            },
            status=e.http_status,
        )
    except Exception as e:
        logger.error(f"models_selection 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def models_switch(request: HttpRequest) -> JsonResponse:
    """POST /api/v1/models/switch/ - 觸發切換 active model"""
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': '無效的 JSON 格式',
                    }
                },
                status=400,
            )

        model_id = validate_model_id(data.get("model_id"))
        force = bool(data.get("force", False))

        available = {m.model_id for m in ModelCatalogService.list_models()}
        if model_id not in available:
            raise TranslationError(ErrorCode.MODEL_NOT_FOUND)

        result = ModelService.switch_model(model_id=model_id, force=force)
        return JsonResponse(result, status=200)

    except TranslationError as e:
        return JsonResponse(
            {
                'error': {
                    'code': e.code,
                    'message': e.message,
                }
            },
            status=e.http_status,
        )
    except Exception as e:
        logger.error(f"models_switch 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500,
        )


@require_http_methods(["GET"])
def admin_status(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/admin/status/

    取得系統狀態（需 IP 白名單）
    """
    # IP 驗證由中介軟體處理
    try:
        from translator.services.model_service import get_model_service
        from translator.services.monitor_service import get_monitor_service
        from translator.services.queue_service import get_queue_service

        monitor_service = get_monitor_service()
        model_service = get_model_service()
        queue_service = get_queue_service()

        # 取得系統狀態
        full_status = monitor_service.get_full_status()

        # 取得模型狀態
        model_status = {
            'loaded': model_service.is_loaded(),
            'name': 'TAIDE-LX-7B',
            'execution_mode': model_service.get_execution_mode() if model_service.is_loaded() else None,
        }

        # 取得佇列狀態
        # QueueService 提供 get_queue_stats()，返回佇列統計字典
        queue_status = queue_service.get_queue_stats()

        return JsonResponse({
            'status': 'ok',
            'timestamp': full_status['timestamp'],
            'system': full_status['system'],
            'resources': {
                'cpu': full_status['cpu'],
                'memory': full_status['memory'],
                'gpu': full_status['gpu'],
                'disk': full_status['disk'],
            },
            'uptime': full_status['uptime'],
            'model': model_status,
            'queue': queue_status,
        })

    except Exception as e:
        logger.error(f"系統狀態 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def admin_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/admin/statistics/

    取得翻譯統計（需 IP 白名單）
    """
    # IP 驗證由中介軟體處理
    try:
        from translator.services.statistics_service import get_statistics_service

        statistics_service = get_statistics_service()
        # 取得可序列化的完整統計字典
        stats = statistics_service.get_full_statistics()

        return JsonResponse({
            'status': 'ok',
            'statistics': stats,
        }, status=200)

    except Exception as e:
        logger.error(f"統計 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@require_http_methods(["GET"])
def health_check(request: HttpRequest) -> JsonResponse:
    """
    GET /api/health/

    健康檢查端點

    用於 Kubernetes/容器編排的健康檢查探針
    回傳系統各元件的健康狀態
    """
    from datetime import datetime
    from translator.services.model_service import get_model_service
    from translator.services.queue_service import get_queue_service
    from translator.utils.logger import get_translator_logger

    translator_logger = get_translator_logger()

    # 執行各項健康檢查
    checks = {}
    overall_status = 'healthy'

    # 1. API 可用性檢查（能回應此請求即為健康）
    checks['api'] = {
        'status': 'healthy',
        'message': 'API 服務運作正常',
    }

    # 2. 翻譯模型檢查
    try:
        model_service = get_model_service()
        model_loaded = model_service.is_loaded()

        if model_loaded:
            checks['translation_model'] = {
                'status': 'healthy',
                'model_name': 'TAIDE-LX-7B',
                'execution_mode': model_service.get_execution_mode(),
                'message': '翻譯模型已載入',
            }
        else:
            checks['translation_model'] = {
                'status': 'degraded',
                'model_name': 'TAIDE-LX-7B',
                'execution_mode': None,
                'message': '翻譯模型尚未載入',
            }
            # 模型未載入時，系統仍可接受請求（將排隊等待）
            if overall_status == 'healthy':
                overall_status = 'degraded'
    except Exception as e:
        checks['translation_model'] = {
            'status': 'unhealthy',
            'model_name': 'TAIDE-LX-7B',
            'message': f'模型檢查失敗: {str(e)}',
        }
        overall_status = 'unhealthy'

    # 3. 佇列服務檢查
    try:
        queue_service = get_queue_service()
        queue_stats = queue_service.get_queue_stats()

        # 佇列目前等待中的請求數命名為 'queued_requests'
        queue_size = queue_stats.get('queued_requests', 0)
        max_queue_size = 1000  # 假設佇列上限

        if queue_size < max_queue_size * 0.8:
            checks['queue'] = {
                'status': 'healthy',
                'queue_size': queue_size,
                'message': '佇列服務運作正常',
            }
        elif queue_size < max_queue_size:
            checks['queue'] = {
                'status': 'degraded',
                'queue_size': queue_size,
                'message': '佇列接近容量上限',
            }
            if overall_status == 'healthy':
                overall_status = 'degraded'
        else:
            checks['queue'] = {
                'status': 'unhealthy',
                'queue_size': queue_size,
                'message': '佇列已滿',
            }
            overall_status = 'unhealthy'
    except Exception as e:
        checks['queue'] = {
            'status': 'unhealthy',
            'message': f'佇列檢查失敗: {str(e)}',
        }
        overall_status = 'unhealthy'

    # 4. 記憶體檢查
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        if memory_percent < 80:
            checks['memory'] = {
                'status': 'healthy',
                'usage_percent': memory_percent,
                'message': '記憶體使用正常',
            }
        elif memory_percent < 90:
            checks['memory'] = {
                'status': 'degraded',
                'usage_percent': memory_percent,
                'message': '記憶體使用較高',
            }
            if overall_status == 'healthy':
                overall_status = 'degraded'
        else:
            checks['memory'] = {
                'status': 'unhealthy',
                'usage_percent': memory_percent,
                'message': '記憶體不足',
            }
            overall_status = 'unhealthy'
    except ImportError:
        checks['memory'] = {
            'status': 'unknown',
            'message': 'psutil 未安裝，無法檢查記憶體',
        }
    except Exception as e:
        checks['memory'] = {
            'status': 'unknown',
            'message': f'記憶體檢查失敗: {str(e)}',
        }

    # 記錄健康檢查
    translator_logger.log_health_check(overall_status, checks)

    # 根據狀態決定 HTTP 狀態碼
    if overall_status == 'healthy':
        http_status = 200
    elif overall_status == 'degraded':
        http_status = 200  # 降級但仍可用
    else:
        http_status = 503  # 服務不可用

    return JsonResponse({
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': checks,
    }, status=http_status)


@require_http_methods(["GET"])
def readiness_probe(request: HttpRequest) -> JsonResponse:
    """
    GET /api/ready/

    就緒探針 - Kubernetes readiness probe

    檢查服務是否準備好接收流量
    - 模型已載入
    - 佇列未滿
    """
    from datetime import datetime
    from translator.services.model_service import get_model_service
    from translator.services.queue_service import get_queue_service

    ready = True
    reasons = []

    # 檢查模型狀態
    try:
        model_service = get_model_service()
        if not model_service.is_loaded():
            ready = False
            reasons.append('翻譯模型尚未載入')
    except Exception as e:
        ready = False
        reasons.append(f'模型服務異常: {str(e)}')

    # 檢查佇列容量
    try:
        queue_service = get_queue_service()
        queue_stats = queue_service.get_queue_stats()
        waiting = queue_stats.get('queued_requests', 0)

        # 如果佇列超過 800 個待處理，暫停接收新請求
        if waiting >= 800:
            ready = False
            reasons.append(f'佇列已滿（{waiting} 個待處理）')
    except Exception as e:
        ready = False
        reasons.append(f'佇列服務異常: {str(e)}')

    # 檢查是否正在關閉
    try:
        from translator.services.shutdown_service import get_shutdown_service
        shutdown_service = get_shutdown_service()
        if shutdown_service.is_shutting_down:
            ready = False
            reasons.append('服務正在關閉中')
    except Exception:
        pass  # 關閉服務未初始化時忽略

    if ready:
        return JsonResponse({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }, status=200)
    else:
        return JsonResponse({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'reasons': reasons,
        }, status=503)


@require_http_methods(["GET"])
def liveness_probe(request: HttpRequest) -> JsonResponse:
    """
    GET /api/live/

    存活探針 - Kubernetes liveness probe

    檢查服務是否存活（能夠回應請求）
    這是最基本的檢查，只要能回應即為存活
    """
    from datetime import datetime

    alive = True
    reasons = []

    # 基本記憶體檢查（避免 OOM）
    try:
        import psutil
        memory = psutil.virtual_memory()

        # 如果記憶體使用超過 95%，可能需要重啟
        if memory.percent > 95:
            alive = False
            reasons.append(f'記憶體使用過高（{memory.percent}%）')
    except ImportError:
        pass  # psutil 未安裝時跳過
    except Exception as e:
        logger.warning(f"存活探針記憶體檢查失敗: {e}")

    if alive:
        return JsonResponse({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }, status=200)
    else:
        return JsonResponse({
            'status': 'not_alive',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'reasons': reasons,
        }, status=503)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def admin_model_load_progress(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/admin/model/load-progress/
    POST /api/v1/admin/model/load-progress/

    取得模型載入進度或觸發模型載入

    GET：取得當前進度（0.0-100.0）
    POST：觸發模型載入（若模型尚未載入）
    """
    try:
        from translator.services.model_service import get_model_service

        model_service = get_model_service()

        if request.method == 'POST':
            # 觸發模型載入
            if model_service.is_loaded():
                return JsonResponse({
                    'status': 'already_loaded',
                    'progress': 100.0,
                    'message': '模型已載入',
                    'model_status': 'loaded',
                }, status=200)

            # 在背景執行緒中載入
            import threading

            def load_in_background():
                model_service.load_model()

            loader_thread = threading.Thread(
                target=load_in_background, daemon=True)
            loader_thread.start()

            return JsonResponse({
                'status': 'loading',
                'progress': model_service.get_loading_progress(),
                'message': '模型載入已啟動',
                'model_status': 'loading',
            }, status=202)

        else:  # GET
            # 取得當前進度
            progress = model_service.get_loading_progress()
            status = model_service.get_status()

            return JsonResponse({
                'status': 'ok',
                'progress': progress,
                'model_status': status,
                'loaded': model_service.is_loaded(),
                'error_message': model_service.get_error_message(),
            }, status=200)

    except Exception as e:
        logger.error(f"模型載入進度 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'error': {
                    'code': ErrorCode.INTERNAL_ERROR,
                    'message': get_error_message(ErrorCode.INTERNAL_ERROR),
                }
            },
            status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def admin_test_model(request: HttpRequest) -> JsonResponse:
    """
    POST /api/v1/admin/model/test/

    測試載入小型模型（例如 gpt2）以驗證當前環境的載入/量化/offload 設定

    請求參數：
    - model_name (可選): 要測試的模型名稱，預設為 'gpt2'

    回應：
    - success: 測試是否成功
    - message: 測試結果訊息
    - model_info: 模型資訊（包括生成的文字、CUDA 可用性等）
    """
    try:
        from translator.services.model_service import get_model_service

        # 解析請求參數
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}

        model_name = data.get('model_name', 'gpt2')

        # 執行測試
        model_service = get_model_service()
        result = model_service.test_load_small_model(model_name)

        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=500)

    except Exception as e:
        logger.error(f"測試模型 API 發生錯誤: {e}", exc_info=True)
        return JsonResponse(
            {
                'success': False,
                'message': f'測試模型時發生錯誤: {str(e)}',
                'model_info': {},
            },
            status=500
        )
