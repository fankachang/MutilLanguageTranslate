"""
多國語言翻譯系統 - 前端頁面視圖

定義所有前端頁面的視圖函數
此檔案為佔位符，實際實作將在後續階段開始
"""

from django.http import HttpResponse
from django.shortcuts import render


def index(request):
    """首頁（翻譯頁面）"""
    # 將在 T021 實作
    return HttpResponse("翻譯頁面（建置中）")


def settings_view(request):
    """設定頁面"""
    # 將在 T036 實作
    return HttpResponse("設定頁面（建置中）")


def admin_status_page(request):
    """系統狀態頁面"""
    # 將在 T047 實作
    return HttpResponse("系統狀態頁面（建置中）")
