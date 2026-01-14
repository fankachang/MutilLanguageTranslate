#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 prompt 格式配置功能

驗證 template 和 chat_template 兩種格式的正確性
"""

import django
import os
import sys
import json

# 設定 Django 環境
sys.path.insert(0, os.path.join(os.path.dirname(
    __file__), '..', 'translation_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'translation_project.settings')

django.setup()


def test_config_loading():
    """測試配置載入"""
    print("\n=== 測試配置載入 ===")

    from translator.services.translation_service import TranslationService

    service = TranslationService()

    print(f"✓ Prompt 格式類型: {service._prompt_format_type}")
    print(f"✓ 是否添加 BOS token: {service._add_bos_token}")
    print(f"✓ 是否使用 system prompt: {service._use_system_prompt}")
    print(
        f"✓ System prompt 內容: {service._system_prompt[:50]}..." if service._system_prompt else "✓ 無 system prompt")

    return True


def test_template_format():
    """測試 template 格式"""
    print("\n=== 測試 template 格式 ===")

    from translator.services.translation_service import TranslationService

    service = TranslationService()

    # 強制使用 template 格式
    original_format = service._prompt_format_type
    service._prompt_format_type = 'template'

    # 測試翻譯 prompt
    prompt = service._build_translation_prompt(
        text="Hello, world!",
        source_language="en",
        target_language="zh-TW"
    )

    print(f"生成的 prompt:\n{prompt}")

    # 驗證格式
    if service._add_bos_token:
        assert '<s>' in prompt, "缺少 BOS token"
        print("✓ BOS token 存在")

    assert '[INST]' in prompt, "缺少 [INST] 標記"
    assert '[/INST]' in prompt, "缺少 [/INST] 標記"
    print("✓ [INST] 標記正確")

    if service._use_system_prompt and service._system_prompt:
        assert '<<SYS>>' in prompt, "缺少 <<SYS>> 標記"
        assert '<</SYS>>' in prompt, "缺少 <</SYS>> 標記"
        print("✓ System prompt 標記正確")

    # 恢復原始格式
    service._prompt_format_type = original_format

    return True


def test_chat_template_format():
    """測試 chat_template 格式"""
    print("\n=== 測試 chat_template 格式 ===")

    from translator.services.translation_service import TranslationService

    service = TranslationService()

    # 強制使用 chat_template 格式
    original_format = service._prompt_format_type
    service._prompt_format_type = 'chat_template'

    # 測試翻譯 prompt
    prompt = service._build_translation_prompt(
        text="Hello, world!",
        source_language="en",
        target_language="zh-TW"
    )

    print(f"生成的 prompt:\n{prompt}")

    # 驗證 JSON 格式
    data = json.loads(prompt)
    assert data.get('_format') == 'chat_template', "格式標記錯誤"
    assert 'messages' in data, "缺少 messages 欄位"
    print("✓ JSON 格式正確")

    messages = data['messages']
    assert len(messages) > 0, "messages 為空"

    # 檢查 role
    roles = [m.get('role') for m in messages]
    assert 'user' in roles, "缺少 user 角色"
    print(f"✓ 角色列表: {roles}")

    # 恢復原始格式
    service._prompt_format_type = original_format

    return True


def test_process_prompt():
    """測試 _process_prompt 方法"""
    print("\n=== 測試 _process_prompt 方法 ===")

    from translator.services.model_providers.local_provider import LocalModelProvider

    provider = LocalModelProvider.__new__(LocalModelProvider)
    provider._tokenizer = None  # 模擬無 tokenizer 情況

    # 測試純文字 prompt
    plain_prompt = "<s>[INST] Hello [/INST]"
    result = provider._process_prompt(plain_prompt)
    assert result == plain_prompt, "純文字 prompt 處理錯誤"
    print("✓ 純文字 prompt 處理正確")

    # 測試 chat_template 格式
    chat_template_prompt = json.dumps({
        "_format": "chat_template",
        "messages": [
            {"role": "system", "content": "You are a translator."},
            {"role": "user", "content": "Translate: Hello"}
        ]
    })
    result = provider._process_prompt(chat_template_prompt)
    print(f"Chat template 處理結果:\n{result}")

    # 驗證回退方案生成的格式
    assert '<s>' in result or '[INST]' in result, "回退方案格式錯誤"
    print("✓ Chat template 回退處理正確")

    return True


def test_fallback_chat_template():
    """測試 _fallback_chat_template 方法"""
    print("\n=== 測試 _fallback_chat_template 方法 ===")

    from translator.services.model_providers.local_provider import LocalModelProvider

    provider = LocalModelProvider.__new__(LocalModelProvider)

    # 測試僅 user 訊息
    messages = [
        {"role": "user", "content": "Hello, world!"}
    ]
    result = provider._fallback_chat_template(messages)
    print(f"僅 user 訊息:\n{result}")
    assert '<s>[INST] Hello, world! [/INST]' in result
    print("✓ 僅 user 訊息格式正確")

    # 測試 system + user 訊息
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, world!"}
    ]
    result = provider._fallback_chat_template(messages)
    print(f"System + user 訊息:\n{result}")
    assert '<<SYS>>' in result
    assert '<</SYS>>' in result
    print("✓ System + user 訊息格式正確")

    # 測試多輪對話
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"}
    ]
    result = provider._fallback_chat_template(messages)
    print(f"多輪對話:\n{result}")
    assert result.count('[INST]') == 2
    assert '</s>' in result
    print("✓ 多輪對話格式正確")

    return True


def main():
    """主測試函數"""
    print("=" * 60)
    print("Prompt 格式配置功能測試")
    print("=" * 60)

    tests = [
        ("配置載入", test_config_loading),
        ("Template 格式", test_template_format),
        ("Chat Template 格式", test_chat_template_format),
        ("_process_prompt 方法", test_process_prompt),
        ("_fallback_chat_template 方法", test_fallback_chat_template),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {name} 測試通過")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} 測試失敗: {e}")

    print("\n" + "=" * 60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
