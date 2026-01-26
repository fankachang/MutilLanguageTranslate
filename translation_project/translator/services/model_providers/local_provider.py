"""
多國語言翻譯系統 - 本地模型提供者

使用 Transformers 在本地載入與推論模型
"""

import logging
import gc
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable

import torch
from django.conf import settings

from translator.enums import ExecutionMode, ModelStatus
from translator.errors import ErrorCode, TranslationError
from .base import BaseModelProvider

logger = logging.getLogger('translator')


class LocalModelProvider(BaseModelProvider):
    """
    本地模型提供者

    使用 Transformers 載入模型到本地記憶體（GPU/CPU）進行推論
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地模型提供者

        Args:
            config: 模型配置
        """
        self._config = config
        self._model = None
        self._tokenizer = None
        self._device: Optional[str] = None
        self._status: str = ModelStatus.NOT_LOADED
        self._error_message: Optional[str] = None
        self._loading_progress: float = 0.0
        self._progress_callback: Optional[Callable[[float, str], None]] = None
        # 記錄實際載入的模型路徑，供模型類型識別使用
        self._loaded_model_path: Optional[Path] = None

    def set_progress_callback(self, callback: Optional[Callable[[float, str], None]]):
        """設定進度回呼函數"""
        self._progress_callback = callback

    def load(self) -> bool:
        """載入模型到本地記憶體"""
        if self._status == ModelStatus.LOADED:
            logger.info("模型已載入，跳過重複載入")
            return True

        if self._status == ModelStatus.LOADING:
            logger.warning("模型正在載入中")
            return False

        self._status = ModelStatus.LOADING
        self._loading_progress = 0.0
        logger.info("開始載入 TAIDE-LX-7B 模型（本地模式）...")
        self._report_progress(5, "初始化配置...")

        smooth_stop = threading.Event()
        smooth_thread: Optional[threading.Thread] = None

        try:
            # 取得模型路徑
            model_path = self._get_model_path()
            self._report_progress(10, f"尋找模型: {model_path}")

            if not model_path.exists():
                raise FileNotFoundError(f"模型路徑不存在: {model_path}")

            # 延遲導入 transformers
            self._report_progress(15, "導入 transformers 套件...")
            from transformers import AutoModelForCausalLM, AutoTokenizer

            def _set_progress_no_log(progress: float, message: str):
                self._loading_progress = float(progress)
                if self._progress_callback:
                    try:
                        self._progress_callback(float(progress), message)
                    except (TypeError, ValueError, RuntimeError):
                        pass

            def _start_smooth_progress(start: int, end: int, message: str, interval_seconds: float = 2.0):
                nonlocal smooth_thread
                if smooth_thread is not None and smooth_thread.is_alive():
                    return

                def _run():
                    current = int(start)
                    target_end = int(end)
                    while not smooth_stop.is_set() and current < target_end:
                        current += 1
                        _set_progress_no_log(current, message)
                        time.sleep(interval_seconds)

                smooth_thread = threading.Thread(target=_run, daemon=True)
                smooth_thread.start()

            # 讀取量化與 offload 選項
            local_config = self._config.get('local', {})
            quant_cfg = local_config.get('quantization', {}) or {}
            enable_4bit_config = bool(quant_cfg.get('enable_4bit', False)) and bool(
                quant_cfg.get('load_in_4bit', False))
            offload_cfg = quant_cfg.get('offload', {}) or {}

            # 偵測 GPU 可用性
            force_cpu = local_config.get('force_cpu', False)

            if torch.cuda.is_available() and not force_cpu:
                self._device = ExecutionMode.GPU

                # 取得 GPU VRAM 大小
                gpu_memory_gb = torch.cuda.get_device_properties(
                    0).total_memory / (1024 ** 3)
                logger.info(
                    f"偵測到 CUDA GPU: {torch.cuda.get_device_name(0)}, VRAM: {gpu_memory_gb:.2f} GB")

                # 自動決定是否使用 4-bit 量化
                auto_enable_4bit = gpu_memory_gb <= 12.0
                enable_4bit = enable_4bit_config if 'enable_4bit' in quant_cfg else auto_enable_4bit

                if enable_4bit:
                    logger.info("GPU VRAM ≤ 12GB，啟用 4-bit 量化以節省記憶體")
                else:
                    logger.info("GPU VRAM > 12GB，使用 float16 模式")

                self._report_progress(20, "使用 GPU 模式，載入模型...")

                max_gpu_memory = local_config.get('max_gpu_memory')
                device_map_config = offload_cfg.get('device_map', 'auto')

                if max_gpu_memory:
                    max_memory = {0: f"{max_gpu_memory}GiB"}
                else:
                    max_memory = None

                # 嘗試 4-bit 量化
                if enable_4bit:
                    try:
                        import bitsandbytes as bnb  # noqa: F401
                        from transformers import BitsAndBytesConfig

                        logger.info("嘗試以 4-bit 量化載入模型 (bitsandbytes)...")
                        self._report_progress(25, "4-bit 量化載入中...")

                        bnb_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.float16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4"
                        )

                        # from_pretrained 可能耗時很久：用平滑進度避免卡在 25
                        _start_smooth_progress(
                            25, 74, "模型權重載入中...", interval_seconds=5.0)

                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            quantization_config=bnb_config,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                        logger.info("✓ 成功使用 4-bit 量化載入模型")
                    except ImportError:
                        logger.warning("bitsandbytes 未安裝，改回 float16 模式")
                        _start_smooth_progress(
                            25, 74, "模型權重載入中...", interval_seconds=5.0)
                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            dtype=torch.float16,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                    except Exception as e:
                        logger.warning(f"4-bit 量化載入失敗，改回非量化載入: {e}")
                        _start_smooth_progress(
                            25, 74, "模型權重載入中...", interval_seconds=5.0)
                        self._model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            dtype=torch.float16,
                            device_map=device_map_config,
                            max_memory=max_memory,
                            trust_remote_code=True,
                        )
                else:
                    # float16 模式
                    self._report_progress(25, "float16 模式載入中...")
                    _start_smooth_progress(
                        25, 74, "模型權重載入中...", interval_seconds=5.0)
                    self._model = AutoModelForCausalLM.from_pretrained(
                        str(model_path),
                        dtype=torch.float16,
                        device_map=device_map_config,
                        max_memory=max_memory,
                        trust_remote_code=True,
                    )
            else:
                self._device = ExecutionMode.CPU
                logger.info("使用 CPU 模式")
                self._report_progress(20, "使用 CPU 模式，載入模型...")

                _start_smooth_progress(
                    20, 74, "模型權重載入中...", interval_seconds=5.0)

                self._model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                )

            # 停止平滑進度，避免後續階段被背景執行緒覆寫
            smooth_stop.set()
            if smooth_thread is not None:
                smooth_thread.join(timeout=1.0)

            # 載入 tokenizer
            self._report_progress(75, "載入 Tokenizer...")
            # Tokenizer 有時也會花一些時間，稍微平滑一下
            smooth_stop.clear()
            _start_smooth_progress(
                75, 94, "Tokenizer 載入中...", interval_seconds=1.0)
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                trust_remote_code=True,
            )

            smooth_stop.set()
            if smooth_thread is not None:
                smooth_thread.join(timeout=1.0)

            # 記錄實際載入的模型路徑
            self._loaded_model_path = model_path

            self._report_progress(95, "模型初始化中...")
            self._status = ModelStatus.LOADED
            self._loading_progress = 100.0
            self._error_message = None
            logger.info(f"模型載入成功，執行模式: {self._device}")
            self._report_progress(100, "模型載入完成！")
            return True

        except Exception as e:
            smooth_stop.set()
            if smooth_thread is not None:
                smooth_thread.join(timeout=1.0)
            self._status = ModelStatus.ERROR
            self._error_message = str(e)
            self._loading_progress = 0.0
            logger.error(f"模型載入失敗: {e}", exc_info=True)
            self._report_progress(0, f"模型載入失敗: {e}")
            return False

    def _process_prompt(self, prompt: str) -> str:
        """
        處理 prompt，支援 template 和 chat_template 兩種格式

        Args:
            prompt: 原始 prompt（可能是純字串或 JSON 格式的 chat_template）

        Returns:
            處理後的 prompt 字串
        """
        import json

        # 嘗試解析為 JSON（chat_template 格式）
        try:
            data = json.loads(prompt)
            if isinstance(data, dict) and data.get('_format') == 'chat_template':
                # 檢查是否為 Translategemma 模型（不支援 system role，需要特殊格式）
                if self._is_translategemma_model():
                    return self._process_translategemma_prompt(data)

                # 使用 tokenizer.apply_chat_template() 處理
                messages = data.get('messages', [])
                if self._tokenizer is not None and hasattr(self._tokenizer, 'apply_chat_template'):
                    # 使用 tokenizer 的 chat template
                    return self._tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True
                    )
                else:
                    # 回退：手動組裝 Llama 2 Chat 格式
                    return self._fallback_chat_template(messages)
        except (json.JSONDecodeError, TypeError):
            # 不是 JSON，直接返回原始 prompt
            pass

        return prompt

    def _is_translategemma_model(self) -> bool:
        """
        檢查當前模型是否為 Translategemma 系列

        Translategemma 有特殊的 chat template 格式要求：
        - 不支援 system role
        - user message content 必須是包含翻譯參數的陣列格式

        使用多種方式來識別：
        1. 實際載入的模型路徑（最可靠）
        2. 配置中指定的模型路徑
        3. 配置中的模型名稱
        """
        # 優先使用實際載入的模型路徑
        loaded_model_path = getattr(self, '_loaded_model_path', None)
        if loaded_model_path is not None:
            path_str = str(loaded_model_path).lower()
            if 'translategemma' in path_str:
                logger.debug("透過實際載入路徑識別為 Translategemma: %s", path_str)
                return True

        # 從配置中取得路徑和名稱
        config = getattr(self, '_config', None)
        if not isinstance(config, dict):
            config = {}

        local_config = config.get('local', {})
        model_name = local_config.get('name', '').lower()
        model_path = local_config.get('path', '').lower()

        is_translategemma = 'translategemma' in model_name or 'translategemma' in model_path

        if is_translategemma:
            logger.debug("透過配置識別為 Translategemma: name=%s, path=%s",
                         model_name, model_path)

        return is_translategemma

    def _normalize_translategemma_lang_code(self, code: Optional[str], fallback: str) -> str:
        """將系統語言代碼正規化為 Translategemma chat_template 可接受的代碼。

        Translategemma 的 chat_template 內建語言表不包含我們系統使用的 `zh-CN`，
        但包含 `zh-Hans`（簡體）與 `zh-Hant`/`zh-TW`（繁體）。

        Args:
            code: 來源/目標語言代碼（可能為 None、auto、含底線）
            fallback: 無法判斷時回退的代碼

        Returns:
            正規化後的語言代碼
        """
        if not code:
            return fallback

        normalized = str(code).strip().replace('_', '-')
        normalized_lower = normalized.lower()

        if normalized_lower == 'auto':
            return fallback

        # 簡體：系統用 zh-CN，Translategemma 以 zh-Hans 表示
        if normalized_lower in {
            'zh-cn',
            'zh-hans',
            'zh-hans-cn',
            'zh-hans-hk',
            'zh-hans-mo',
            'zh-hans-my',
            'zh-hans-sg',
        }:
            return 'zh-Hans'

        # 繁體：系統主要用 zh-TW；若帶其他繁體變體也統一
        if normalized_lower in {
            'zh-tw',
            'zh-hant',
            'zh-hant-hk',
            'zh-hant-mo',
            'zh-hant-my',
        }:
            return 'zh-TW'

        # 其他語言（en/ja/ko/fr/de/es）直接回傳（保留原大小寫以利對照）
        return normalized

    def _process_translategemma_prompt(self, data: dict) -> str:
        """
        處理 Translategemma 模型的特殊 prompt 格式

        Translategemma 的 chat template 要求：
        1. 對話必須以 user 開頭（不支援 system role）
        2. user message 的 content 必須是特殊格式的陣列：
           [{"type": "text", "source_lang_code": "en", "target_lang_code": "zh-TW", "text": "..."}]

        Args:
            data: 包含 messages、source_lang_code、target_lang_code、text 的字典

        Returns:
            處理後的 prompt 字串
        """
        # Translategemma chat_template 的語言對照表不包含 zh-CN，因此先正規化
        source_lang = self._normalize_translategemma_lang_code(
            data.get('source_lang_code', 'en'),
            fallback='en',
        )
        target_lang = self._normalize_translategemma_lang_code(
            data.get('target_lang_code', 'zh-TW'),
            fallback='zh-TW',
        )
        text = data.get('text', '')

        # 建構 Translategemma 格式的 messages
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "source_lang_code": source_lang,
                "target_lang_code": target_lang,
                "text": text
            }]
        }]

        logger.debug(
            "Translategemma 格式 messages: source=%s, target=%s",
            source_lang, target_lang
        )

        if self._tokenizer is not None and hasattr(self._tokenizer, 'apply_chat_template'):
            return self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Translategemma 必須使用 tokenizer
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                "Translategemma 模型需要 tokenizer 支援 apply_chat_template"
            )

    def _fallback_chat_template(self, messages: list) -> str:
        """
        當 tokenizer 不支援 apply_chat_template 時的回退方案
        手動組裝 Llama 2 Chat 格式

        Args:
            messages: 訊息列表 [{"role": "...", "content": "..."}]

        Returns:
            組裝後的 prompt 字串
        """
        prompt_parts = []
        system_content = None

        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')

            if role == 'system':
                system_content = content
            elif role == 'user':
                if system_content:
                    # 將 system prompt 嵌入第一個 user message
                    prompt_parts.append(
                        f"<s>[INST] <<SYS>>\n{system_content}\n<</SYS>>\n\n{content} [/INST]"
                    )
                    system_content = None
                else:
                    prompt_parts.append(f"<s>[INST] {content} [/INST]")
            elif role == 'assistant':
                prompt_parts.append(f" {content} </s>")

        return ''.join(prompt_parts)

    def generate(
        self,
        prompt: str,
        generation_params: Dict[str, Any],
    ) -> str:
        """執行文字生成"""
        if not self.is_loaded():
            raise TranslationError(ErrorCode.MODEL_NOT_LOADED)

        if self._tokenizer is None or self._model is None:
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                "模型或 tokenizer 尚未初始化",
            )

        tokenizer = self._tokenizer
        model = self._model

        try:
            # 檢查是否為 chat_template 格式
            actual_prompt = self._process_prompt(prompt)

            # 編碼輸入
            inputs = tokenizer(
                actual_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,
            )

            # 移除尾端可能的 eos_token
            input_ids = inputs.get('input_ids')
            attention_mask = inputs.get('attention_mask')
            eos_id = tokenizer.eos_token_id
            if input_ids is not None and eos_id is not None and input_ids.shape[-1] > 0:
                if int(input_ids[0, -1]) == int(eos_id):
                    inputs['input_ids'] = input_ids[:, :-1]
                    if attention_mask is not None and attention_mask.shape[-1] == input_ids.shape[-1]:
                        inputs['attention_mask'] = attention_mask[:, :-1]

            # 移動到正確的設備
            if self._device == ExecutionMode.GPU:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # 執行生成
            with torch.no_grad():
                from transformers import GenerationConfig

                generation_config = GenerationConfig(**generation_params)

                # Translategemma 使用 <end_of_turn> 標記回合結束；若只用 <eos> 容易生成到回合外造成尾巴雜訊
                eos_token_id = tokenizer.eos_token_id
                pad_token_id = tokenizer.pad_token_id

                if self._is_translategemma_model():
                    try:
                        end_of_turn_id = tokenizer.convert_tokens_to_ids(
                            '<end_of_turn>')
                        unk_id = tokenizer.unk_token_id
                        if end_of_turn_id is not None and (unk_id is None or int(end_of_turn_id) != int(unk_id)):
                            # transformers 支援 list eos_token_id：遇到任一個即停止
                            eos_token_id = [int(end_of_turn_id)]
                            if tokenizer.eos_token_id is not None:
                                eos_token_id.append(
                                    int(tokenizer.eos_token_id))
                    except Exception:  # pylint: disable=broad-exception-caught
                        pass

                if pad_token_id is None:
                    if isinstance(eos_token_id, list) and eos_token_id:
                        pad_token_id = int(eos_token_id[0])
                    else:
                        pad_token_id = tokenizer.eos_token_id

                generate_kwargs = {
                    **inputs,
                    'generation_config': generation_config,
                    'pad_token_id': pad_token_id,
                    'eos_token_id': eos_token_id,
                }

                if 'early_stopping' not in generate_kwargs and generation_params.get('num_beams', 1) > 1:
                    generate_kwargs['early_stopping'] = True

                outputs = model.generate(**generate_kwargs)

            # 只解碼新生成的 token
            prompt_len = int(inputs['input_ids'].shape[-1])
            generated_ids = outputs[0][prompt_len:]
            generated_text = tokenizer.decode(
                generated_ids,
                skip_special_tokens=True,
            ).strip()

            logger.debug(
                "generate() 完成（本地模式）| new_tokens=%d | preview=%r",
                int(generated_ids.shape[-1]
                    ) if hasattr(generated_ids, 'shape') else -1,
                generated_text[:200],
            )

            return generated_text

        except Exception as e:
            logger.error(f"文字生成失敗: {e}", exc_info=True)
            raise TranslationError(
                ErrorCode.INTERNAL_ERROR,
                f"文字生成失敗: {str(e)}"
            )

    def is_loaded(self) -> bool:
        """檢查模型是否已載入"""
        return self._status == ModelStatus.LOADED

    def get_status(self) -> str:
        """取得模型狀態"""
        return self._status

    def get_execution_mode(self) -> str:
        """取得執行模式"""
        return self._device or ExecutionMode.CPU

    def get_error_message(self) -> Optional[str]:
        """取得錯誤訊息"""
        return self._error_message

    def get_loading_progress(self) -> float:
        """取得載入進度"""
        return self._loading_progress

    def unload(self):
        """卸載模型"""
        if self._model is not None:
            model = self._model
            self._model = None
            del model

        if self._tokenizer is not None:
            tokenizer = self._tokenizer
            self._tokenizer = None
            del tokenizer

        # 先觸發 GC，確保 Python 層引用真正釋放
        gc.collect()

        if torch.cuda.is_available():
            # 同步避免尚未完成的 kernel 導致 cache 無法回收
            try:
                torch.cuda.synchronize()
            except RuntimeError:  # pragma: no cover
                pass

            try:
                torch.cuda.empty_cache()
            except RuntimeError:  # pragma: no cover
                pass

            # 回收 IPC 相關的共享記憶體（有些情境下能再釋放一些保留量）
            try:
                torch.cuda.ipc_collect()
            except (AttributeError, RuntimeError):  # pragma: no cover
                pass

        # 再做一次 GC，確保清理後的物件釋放
        gc.collect()

        self._status = ModelStatus.NOT_LOADED
        self._device = None
        self._loaded_model_path = None
        logger.info("模型已卸載（本地模式）")

    def _report_progress(self, progress: float, message: str):
        """回報載入進度"""
        self._loading_progress = progress
        logger.info(f"模型載入進度: {progress:.1f}% - {message}")

        if self._progress_callback:
            try:
                self._progress_callback(progress, message)
            except Exception as e:
                logger.error(f"進度回呼執行失敗: {e}")

    def _get_model_path(self) -> Path:
        """取得模型路徑"""
        local_config = self._config.get('local', {})
        model_rel_path = local_config.get(
            'path',
            'models/TAIDE-LX-7B-Chat'
        )

        project_root = settings.PROJECT_ROOT
        return project_root / model_rel_path
