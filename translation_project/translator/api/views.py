"""
多國語言翻譯系統 - API 視圖

定義所有 REST API 端點的視圖函數
此檔案為佔位符，實際實作將在 Phase 3 (US1) 開始
"""

from django.http import JsonResponse


def translate(request):
    """POST /api/v1/translate/ - 執行文字翻譯"""
    # 將在 T018 實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


def translate_status(request, request_id):
    """GET /api/v1/translate/{request_id}/status/ - 查詢翻譯狀態"""
    # 將在 T018b 實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


def languages(request):
    """GET /api/v1/languages/ - 取得語言清單"""
    # 將在 T025 實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


def admin_status(request):
    """GET /api/v1/admin/status/ - 取得系統狀態"""
    # 將在 T044 實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


def admin_statistics(request):
    """GET /api/v1/admin/statistics/ - 取得翻譯統計"""
    # 將在 T045 實作
    return JsonResponse({'status': 'not_implemented'}, status=501)


def health_check(request):
    """GET /api/health/ - 健康檢查"""
    # 將在 T050 實作
    return JsonResponse({
        'status': 'healthy',
        'message': '服務運行中（基礎設施建置階段）',
    })
