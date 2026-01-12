"""
翻譯系統頁面視圖
Pages views for the translation system

負責渲染前端頁面，注入必要資料
"""

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from translator.utils.config_loader import ConfigLoader


def get_languages_for_template():
    """
    取得語言列表，用於模板渲染
    
    Returns:
        list: 語言列表，包含 code 和 name
    """
    config_loader = ConfigLoader()
    languages = config_loader.get_languages()
    return [{'code': lang.code, 'name': lang.name} for lang in languages]


def get_default_target_language():
    """
    取得預設目標語言
    
    Returns:
        str: 預設目標語言代碼
    """
    config_loader = ConfigLoader()
    app_config = config_loader.get_app_config()
    return app_config.get('translation', {}).get('default_target_language', 'en')


@require_http_methods(["GET"])
def index(request):
    """
    首頁 - 翻譯功能主頁面
    
    渲染翻譯頁面，注入語言列表和預設設定
    """
    context = {
        'languages': get_languages_for_template(),
        'default_target_lang': get_default_target_language(),
        'page_title': '多國語言翻譯系統',
    }
    return render(request, 'translator/index.html', context)


@require_http_methods(["GET"])
def history(request):
    """
    歷史記錄頁面
    
    顯示使用者的翻譯歷史（前端 sessionStorage 儲存）
    """
    context = {
        'languages': get_languages_for_template(),
        'page_title': '歷史記錄',
    }
    return render(request, 'translator/history.html', context)


@require_http_methods(["GET"])
def settings_view(request):
    """
    設定頁面
    
    讓使用者調整偏好設定（前端 sessionStorage 儲存）
    """
    context = {
        'languages': get_languages_for_template(),
        'page_title': '設定',
    }
    return render(request, 'translator/settings.html', context)


@require_http_methods(["GET"])
def help_page(request):
    """
    說明頁面
    
    提供使用說明和常見問題
    """
    context = {
        'page_title': '使用說明',
    }
    return render(request, 'translator/help.html', context)


@require_http_methods(["GET"])
def admin_status_page(request):
    """
    系統狀態頁面（管理介面）
    
    顯示系統資源使用狀況、翻譯統計等監控資訊
    注意：此頁面透過 IP 白名單中介軟體保護
    """
    context = {
        'page_title': '系統狀態監控',
    }
    return render(request, 'translator/admin_status.html', context)
