"""
多國語言翻譯系統 - API URL 路由

定義 API v1 的所有端點
"""

from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    # 翻譯 API
    path('translate/', views.translate, name='translate'),
    path(
        'translate/<uuid:request_id>/status/',
        views.translate_status,
        name='translate_status'
    ),
    
    # 語言 API
    path('languages/', views.languages, name='languages'),
    
    # 管理 API（需 IP 白名單）
    path('admin/status/', views.admin_status, name='admin_status'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),
    path('admin/model/load-progress/', views.admin_model_load_progress, name='admin_model_load_progress'),
    path('admin/model/test/', views.admin_test_model, name='admin_test_model'),
]
