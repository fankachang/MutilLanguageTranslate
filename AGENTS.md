# Base Rule

* **Response Language:** `zh-TW`
* All specifications, plans, and user-facing documentation MUST be written in Traditional Chinese (zh-TW), ONLY constitution MUST in English.
* When drafting the constitution, the context MUST be translated into "constitution_zhTW.md" and placed in the same directory (please note that file names are case-sensitive).
* Git Log, Code annotations MUST be written in Traditional Chinese (zh-TW).

# 開發準則

* 前端呼叫後端 API/Function 時，需要確保後端有該 API/Function，不可胡亂自行命名/腦補
* 不要過度設計或是過度開發
* 開發時，前端界面需要考量界面高度，輸入欄位、元件等位置要考慮一致性。

# Terminal 使用規範

* **禁止在背景服務的 Terminal 中執行其他指令**
  - 當使用 `isBackground=true` 啟動服務（如 Django runserver、模型載入）後，該 Terminal 專屬於該服務
  - 不可在同一個 Terminal 執行任何其他指令（包括 `Start-Sleep`、`curl`、`ls` 等）
  - 執行其他指令會導致背景服務被中斷或終止

* **檢查服務狀態的正確方式**
  - 使用 `get_terminal_output` 工具查看背景服務的輸出
  - 在**新的 Terminal** 中執行測試指令（如 `curl`、健康檢查）
  - 使用 `open_simple_browser` 在瀏覽器中驗證服務

* **等待服務啟動的正確方式**
  - 啟動背景服務後，使用 `get_terminal_output` 定期檢查載入進度
  - 不要使用 `Start-Sleep` 在同一個 Terminal 等待
  - 如需等待，應在不同的 Terminal 或使用輪詢機制檢查服務狀態

* **範例：正確的服務啟動與檢查流程**
  ```
  1. Terminal A: 啟動背景服務 (isBackground=true)
  2. 使用 get_terminal_output(Terminal A ID) 檢查啟動狀態
  3. Terminal B (新): 執行健康檢查 curl http://localhost:8000/api/health/
  4. 繼續使用 get_terminal_output(Terminal A ID) 監控服務日誌
  ```

* **錯誤示範（禁止）**
  ```
  ❌ Terminal A: 啟動背景服務 (isBackground=true)
  ❌ Terminal A: Start-Sleep -Seconds 60  # 這會中斷背景服務！
  ❌ Terminal A: curl http://localhost:8000/  # 這也會中斷！
  ```