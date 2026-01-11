"""
多國語言翻譯系統 - IP 白名單中介軟體

本模組負責驗證管理頁面的 IP 存取權限：
- CIDR 格式解析
- 內網/管理員 IP 驗證
"""

import ipaddress
import json
import logging
from typing import List, Optional

from django.http import HttpRequest, JsonResponse

from translator.errors import ErrorCode, get_error_message
from translator.utils.config_loader import ConfigLoader

logger = logging.getLogger('translator')


class IPWhitelistMiddleware:
    """
    IP 白名單中介軟體
    
    驗證管理頁面（/api/v1/admin/*）的 IP 存取權限。
    支援 CIDR 格式的 IP 範圍設定。
    """
    
    # 需要驗證的路徑前綴
    PROTECTED_PATHS = [
        '/api/v1/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._networks: Optional[List[ipaddress.IPv4Network]] = None
    
    def __call__(self, request: HttpRequest):
        # 檢查是否需要驗證
        if self._requires_verification(request.path):
            client_ip = self._get_client_ip(request)
            
            if not self._is_allowed(client_ip):
                logger.warning(
                    f"IP 存取被拒絕: {client_ip} 嘗試存取 {request.path}"
                )
                return JsonResponse(
                    {
                        'error': {
                            'code': ErrorCode.ACCESS_DENIED,
                            'message': get_error_message(ErrorCode.ACCESS_DENIED),
                        }
                    },
                    status=403,
                )
        
        return self.get_response(request)
    
    def _requires_verification(self, path: str) -> bool:
        """
        檢查路徑是否需要 IP 驗證
        
        Args:
            path: 請求路徑
            
        Returns:
            是否需要驗證
        """
        return any(path.startswith(prefix) for prefix in self.PROTECTED_PATHS)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        取得客戶端 IP
        
        支援透過 proxy 的情況，優先使用 X-Forwarded-For 標頭。
        
        Args:
            request: HTTP 請求
            
        Returns:
            客戶端 IP 字串
        """
        # 優先使用 X-Forwarded-For（如果有 proxy）
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 取第一個 IP（最原始的客戶端 IP）
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
    
    def _is_allowed(self, ip: str) -> bool:
        """
        檢查 IP 是否在白名單中
        
        Args:
            ip: IP 位址
            
        Returns:
            是否允許存取
        """
        if not ip:
            return False
        
        try:
            client_ip = ipaddress.ip_address(ip)
        except ValueError:
            logger.warning(f"無效的 IP 位址: {ip}")
            return False
        
        # 載入白名單網路
        networks = self._get_networks()
        
        # 檢查是否在任一允許的網路中
        for network in networks:
            try:
                if client_ip in network:
                    return True
            except TypeError:
                # IPv4/IPv6 混合的情況
                continue
        
        return False
    
    def _get_networks(self) -> List[ipaddress.IPv4Network]:
        """
        取得允許的網路列表
        
        Returns:
            IPv4Network 列表
        """
        if self._networks is None:
            self._networks = []
            allowed_ips = ConfigLoader.get_admin_allowed_ips()
            
            for cidr in allowed_ips:
                try:
                    network = ipaddress.ip_network(cidr, strict=False)
                    self._networks.append(network)
                except ValueError as e:
                    logger.warning(f"無效的 CIDR 格式: {cidr} - {e}")
        
        return self._networks
    
    def reload_whitelist(self):
        """重新載入白名單（用於配置更新時）"""
        self._networks = None
        logger.info("IP 白名單已重新載入")


def is_ip_allowed(ip: str) -> bool:
    """
    工具函數：檢查 IP 是否在白名單中
    
    可用於視圖函數中進行額外的 IP 驗證。
    
    Args:
        ip: IP 位址
        
    Returns:
        是否允許存取
    """
    allowed_ips = ConfigLoader.get_admin_allowed_ips()
    
    try:
        client_ip = ipaddress.ip_address(ip)
    except ValueError:
        return False
    
    for cidr in allowed_ips:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            if client_ip in network:
                return True
        except (ValueError, TypeError):
            continue
    
    return False
