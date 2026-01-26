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

    # 模型 API（US1）
    path('models/', views.models_list, name='models_list'),
    path('models/selection/', views.models_selection, name='models_selection'),
    path('models/switch/', views.models_switch, name='models_switch'),

    # 公開狀態 API（US2，匿名可用）
    path('status/', views.public_status, name='public_status'),
    path('statistics/', views.public_statistics, name='public_statistics'),
    path('model/load-progress/', views.public_model_load_progress,
         name='public_model_load_progress'),

    # 管理 API（需 IP 白名單）
    path('admin/status/', views.admin_status, name='admin_status'),
    path('admin/statistics/', views.admin_statistics, name='admin_statistics'),
    path('admin/model/load-progress/', views.admin_model_load_progress,
         name='admin_model_load_progress'),
    path('admin/model/unload/', views.admin_model_unload,
         name='admin_model_unload'),
    path('admin/model/test/', views.admin_test_model, name='admin_test_model'),
]
