"""
獨立測試 TAIDE-LX-7B-Chat 模型載入
不透過 Django，直接測試 transformers 載入
"""

import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_model_loading():
    """測試模型載入"""
    model_path = "models/TAIDE-LX-7B-Chat"

    logger.info("=" * 60)
    logger.info("開始測試 TAIDE-LX-7B-Chat 模型載入")
    logger.info("=" * 60)

    # 檢查 CUDA
    if torch.cuda.is_available():
        logger.info(f"✓ CUDA 可用")
        logger.info(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        logger.info(
            f"✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        logger.warning("✗ CUDA 不可用，將使用 CPU")

    # 配置 4-bit 量化
    logger.info("\n配置 4-bit 量化...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4"
    )

    # 載入 Tokenizer
    logger.info(f"\n載入 Tokenizer from {model_path}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info("✓ Tokenizer 載入成功")
    except Exception as e:
        logger.error(f"✗ Tokenizer 載入失敗: {e}")
        return False

    # 載入模型
    logger.info(f"\n載入模型 from {model_path}（4-bit 量化）...")
    logger.info("這可能需要 1-2 分鐘，請耐心等待...")

    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        logger.info("✓ 模型載入成功！")

        # 顯示模型資訊
        if torch.cuda.is_available():
            logger.info(
                f"✓ 使用記憶體: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
            logger.info(
                f"✓ 保留記憶體: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")

        # 簡單測試
        logger.info("\n執行簡單推論測試...")
        test_prompt = "<s>[INST] 請將以下英文翻譯成繁體中文：Hello [/INST]"
        inputs = tokenizer(test_prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.3,
                do_sample=True
            )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"✓ 推論結果: {result}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有測試通過！模型可正常使用")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"\n✗ 模型載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_model_loading()
    exit(0 if success else 1)
