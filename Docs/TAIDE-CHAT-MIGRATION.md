# TAIDE-LX-7B-Chat 模型切換說明

## 修改時間
2026-01-14

## 修改內容

### 1. 模型配置更新 ([model_config.yaml](config/model_config.yaml))

```yaml
provider:
  local:
    name: "TAIDE-LX-7B-Chat"          # 原: TAIDE-LX-7B
    path: "models/TAIDE-LX-7B-Chat"   # 原: models/models--taide--TAIDE-LX-7B/snapshots/...
```

### 2. Prompt 格式更新

#### 配置檔 ([model_config.yaml](config/model_config.yaml))
- 採用標準 Llama 2 Chat 格式：`<s>[INST] 指令 [/INST] 回應 </s>`
- **關鍵變更**：`[/INST]` 後面**不加任何提示詞**（如「譯文：」）
- 使用 YAML `|-` 語法移除尾部換行符

```yaml
prompts:
  translation: |-
    [INST] 你是專業翻譯員。你的任務是『翻譯』，不是改寫、續寫或創作。
    請將下列文字從 {source_language} 翻譯成 {target_language}。

    要求：
    - 只輸出譯文本身，不要輸出「譯文：」等前綴
    - 不要輸出任何解釋、補充說明或延伸內容
    - 不要產生章節、標題、目錄或無關文字
    - 保持原文的行數和結構，不要增加或刪減內容

    原文：
    {text} [/INST]
```

#### 程式碼 ([translation_service.py](translation_project/translator/services/translation_service.py))
- 修改 `__init__()` 載入配置檔的 Prompt 範本
- 修改 `_build_translation_prompt()` 使用配置檔範本並動態替換變數
- 自動添加 BOS token (`<s>`)
- 重試場景的額外約束會插入到 `[/INST]` **之前**

### 3. 關鍵差異對比

| 項目         | 舊版 (TAIDE-LX-7B)           | 新版 (TAIDE-LX-7B-Chat)      |
| ------------ | ---------------------------- | ---------------------------- |
| 模型類型     | 預訓練模型                   | 指令微調 (Instruction Tuned) |
| Prompt 格式  | `[INST] ... [/INST]\n譯文：` | `<s>[INST] ... [/INST]`      |
| BOS Token    | 未明確添加                   | 明確添加 `<s>`               |
| 配置檔範本   | 未使用                       | **使用配置檔範本**           |
| [/INST] 後綴 | 有提示詞「譯文：」           | **無任何提示詞**             |

## 為什麼要移除 [/INST] 後的提示詞？

TAIDE-LX-7B-Chat 是基於 Llama 2 的對話微調模型，標準格式為：

```
<s>[INST] 指令 [/INST] 回應 </s>
```

模型在訓練時學習到 `[/INST]` 後**立即開始生成回應**，如果加上「譯文：」等提示詞：
- ❌ 模型可能把它當作已生成的內容，導致續寫行為
- ❌ 可能產生「譯文：譯文：...」重複前綴
- ✅ 正確做法：讓模型在 `[/INST]` 後自由生成

## 測試驗證

執行測試腳本：
```bash
python test_taide_chat.py
```

測試項目：
- ✅ 配置檔正確載入
- ✅ Prompt 格式符合 Llama 2 Chat 規範
- ✅ BOS token (`<s>`) 正確添加
- ✅ `[/INST]` 後面無多餘提示詞
- ✅ Prompt 注入防護正常運作
- ✅ 重試場景的額外約束正確插入

## 使用方式

無需修改 API 呼叫方式，系統會自動：
1. 從配置檔載入 Prompt 範本
2. 根據來源/目標語言替換變數
3. 添加 BOS token
4. 套用 Prompt 注入防護
5. 呼叫 TAIDE-LX-7B-Chat 模型生成翻譯

## 相關檔案

- [config/model_config.yaml](config/model_config.yaml) - 模型與 Prompt 配置
- [translation_project/translator/services/translation_service.py](translation_project/translator/services/translation_service.py) - 翻譯服務實作
- [test_taide_chat.py](test_taide_chat.py) - 驗證測試腳本
- [models/TAIDE-LX-7B-Chat/](models/TAIDE-LX-7B-Chat/) - 模型檔案目錄
