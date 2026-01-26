"""單元測試 - Translategemma 語言代碼正規化

問題背景：
- 我們系統使用 zh-CN 表示簡體中文
- Translategemma 的 chat_template 內建語言表不包含 zh-CN（但包含 zh-Hans）
- 若直接傳 zh-CN 會在套用 chat template 時拋出例外

此測試確保 LocalModelProvider 在 Translategemma 模式下會先把語言碼正規化。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 加入專案路徑（比照既有 unit tests 的做法）
sys.path.insert(0, os.path.join(os.path.dirname(
    __file__), "../../translation_project"))


class _StubTokenizer:
    def __init__(self):
        self.last_messages = None

    def apply_chat_template(self, messages, *_args, **_kwargs):
        self.last_messages = messages
        return "PROMPT_OK"


def _make_provider():
    from translator.services.model_providers.local_provider import LocalModelProvider

    provider = LocalModelProvider(
        {"local": {"path": "models/Translategemma-4b-it"}})
    provider._tokenizer = _StubTokenizer()
    provider._loaded_model_path = Path("models/Translategemma-4b-it")
    return provider


def test_translategemma_normalizes_zh_cn_to_zh_hans():
    provider = _make_provider()

    prompt = json.dumps(
        {
            "_format": "chat_template",
            "messages": [{"role": "user", "content": "ignored"}],
            "source_lang_code": "zh-CN",
            "target_lang_code": "en",
            "text": "我愛你",
        },
        ensure_ascii=False,
    )

    result = provider._process_prompt(prompt)
    assert result == "PROMPT_OK"

    messages = provider._tokenizer.last_messages
    assert messages and messages[0]["role"] == "user"
    content0 = messages[0]["content"][0]
    assert content0["source_lang_code"] == "zh-Hans"
    assert content0["target_lang_code"] == "en"


def test_translategemma_normalizes_zh_cn_underscore_variant():
    provider = _make_provider()

    prompt = json.dumps(
        {
            "_format": "chat_template",
            "messages": [{"role": "user", "content": "ignored"}],
            "source_lang_code": "zh_CN",
            "target_lang_code": "en",
            "text": "我愛你",
        },
        ensure_ascii=False,
    )

    provider._process_prompt(prompt)

    content0 = provider._tokenizer.last_messages[0]["content"][0]
    assert content0["source_lang_code"] == "zh-Hans"


def test_translategemma_keeps_zh_tw_as_zh_tw():
    provider = _make_provider()

    prompt = json.dumps(
        {
            "_format": "chat_template",
            "messages": [{"role": "user", "content": "ignored"}],
            "source_lang_code": "zh-TW",
            "target_lang_code": "en",
            "text": "我愛你",
        },
        ensure_ascii=False,
    )

    provider._process_prompt(prompt)

    content0 = provider._tokenizer.last_messages[0]["content"][0]
    assert content0["source_lang_code"] == "zh-TW"
