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
from translator.utils.config_loader import ConfigLoader

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
        
        # 建立翻譯請求
        translation_request = TranslationRequest(
            text=text,
            source_language=source_language,
            target_language=target_language,
            quality=quality,
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
def admin_status(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/admin/status/
    
    取得系統狀態（需 IP 白名單）
    """
    # IP 驗證由中介軟體處理
    # 將在 T044 完整實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


@require_http_methods(["GET"])
def admin_statistics(request: HttpRequest) -> JsonResponse:
    """
    GET /api/v1/admin/statistics/
    
    取得翻譯統計（需 IP 白名單）
    """
    # IP 驗證由中介軟體處理
    # 將在 T045 完整實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


@require_http_methods(["GET"])
def health_check(request: HttpRequest) -> JsonResponse:
    """
    GET /api/health/
    
    健康檢查端點
    """
    # 將在 T050 完整實作
    from datetime import datetime
    from translator.services.model_service import get_model_service
    
    model_service = get_model_service()
    
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'checks': {
            'api': {
                'status': 'healthy',
            },
            'translation_model': {
                'status': 'healthy' if model_service.is_loaded() else 'not_loaded',
                'model_name': 'TAIDE-LX-7B',
            },
        },
    })
