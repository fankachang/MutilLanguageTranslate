"""
多國語言翻譯系統 - 前端頁面 URL 路由

定義所有前端頁面的路由
"""

from django.urls import path

from . import views

app_name = 'translator'

urlpatterns = [
    # 首頁（翻譯頁面）
    path('', views.index, name='index'),
    
    # 歷史記錄頁面
    path('history/', views.history, name='history'),
    
    # 設定頁面
    path('settings/', views.settings_view, name='settings'),
    
    # 說明頁面
    path('help/', views.help_page, name='help'),
    
    # 系統狀態頁面（管理用）
    path('admin/status/', views.admin_status_page, name='admin_status_page'),
]

