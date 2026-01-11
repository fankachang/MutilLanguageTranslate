---
name:"RunPowerShell"
title: "Copilot 啟動 PowerShell 初始設定"
id: "Copilot-InitPowerShell"
description: "設定 PowerShell 的 UTF-8 編碼以避免中文亂碼，適用於 Copilot 啟動時的初始設定。"
level: "基礎"
estimated_time: "2-5 分鐘"
last_updated: "2026-01-06"
learning_goals:
  - "理解為何需要設定 PowerShell 的 UTF-8 編碼"
  - "學會執行初始設定指令"
  - "確保 Copilot 啟動 PowerShell 時中文顯示正常"
quick_start:
  - step: "執行以下指令以設定 UTF-8 編碼"
    commands: |
      chcp 65001 > $null
      $OutputEncoding = [Console]::OutputEncoding = [Console]::InputEncoding = [System.Text.Encoding]::UTF8
      $PSDefaultParameterValues['*:Encoding'] = 'utf8'
    explanation: "切換代碼頁並設定輸入/輸出與 Cmdlet 預設編碼為 UTF-8"
verification:
  - "Write-Output \"測試中文輸出：你好，世界！\""
  - "[Console]::OutputEncoding.EncodingName"
faq:
  - q: "為什麼需要執行這些指令？"
    a: |
      預設情況下，PowerShell 的編碼可能不是 UTF-8，導致中文顯示亂碼。這些指令確保輸入與輸出皆使用 UTF-8 編碼。
  - q: "是否需要每次啟動都執行？"
    a: |
      若將這些指令加入 PowerShell Profile，則每次啟動時會自動執行，無需手動輸入。
resources:
  - "https://learn.microsoft.com/zh-tw/powershell/"
  - "https://learn.microsoft.com/zh-tw/powershell/module/microsoft.powershell.core/about/about_character_encoding"
checklist:
  - "[ ] 我已執行初始設定指令"
  - "[ ] 我已驗證中文顯示正常"
  - "[ ] （選用）我已將設定加入 PowerShell Profile"
---