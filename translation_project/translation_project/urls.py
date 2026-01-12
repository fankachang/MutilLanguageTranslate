"""
URL configuration for translation_project project.

多國語言翻譯系統 URL 路由配置
"""

from django.contrib import admin
from django.urls import include, path

from translator.api.views import health_check, liveness_probe, readiness_probe

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/', include('translator.api.urls')),
    
    # 健康檢查
    path('api/health/', health_check, name='health_check'),
    
    # Kubernetes 探針
    path('api/ready/', readiness_probe, name='readiness_probe'),
    path('api/live/', liveness_probe, name='liveness_probe'),
    
    # 前端頁面（將在後續實作）
    path('', include('translator.urls')),
]
