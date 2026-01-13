"""
多國語言翻譯系統 - 模型提供者

本模組定義模型推論的抽象介面與實作：
- BaseModelProvider: 抽象基礎類別
- LocalModelProvider: 本地 Transformers 模型載入
- RemoteAPIProvider: 遠端 API 呼叫（OpenAI 相容 / HuggingFace Inference）
"""

from .base import BaseModelProvider
from .local_provider import LocalModelProvider
from .remote_provider import RemoteAPIProvider

__all__ = [
    'BaseModelProvider',
    'LocalModelProvider',
    'RemoteAPIProvider',
]
