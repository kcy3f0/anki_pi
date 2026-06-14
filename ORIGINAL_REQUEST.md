# Original User Request

## Initial Request — 2026-06-14T07:53:27+08:00

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Delegate to teamwork_preview and execute task

對 `anki_pi` 專案進行全面的程式碼審查，找出並記錄至少 20 個潛在錯誤（涵蓋安全漏洞、邏輯錯誤、執行期錯誤及程式碼品質問題）。

Working directory: c:\Users\kcy3f\anki_pi
Integrity mode: benchmark

## Requirements

### R1. 全面程式碼審查與錯誤報告
團隊需要對整個 `anki_pi` 專案進行靜態程式碼審查，並產出一份詳細的錯誤報告（建議檔名：`bug_report.md`）。團隊僅需產出報告，**絕對不可以**修改專案內的任何原始碼檔案。

### R2. 找出至少 20 個錯誤
報告中必須包含至少 20 個獨立且具體的錯誤。這些錯誤可以是安全漏洞、邏輯錯誤、潛在的執行期崩潰，或重大的程式碼品質問題。

### R3. 錯誤記錄格式
對於每一個錯誤，報告 must 明確指出發生錯誤的檔案路徑與行號，透過邏輯推導解釋該程式碼為何會導致錯誤，並提供具體的修復建議。

### R4. 環境與工具限制
如果團隊在審查過程中需要安裝任何 Python 套件（例如執行 pylint 或其他分析工具），必須在專案目錄下建立並使用 Python 虛擬環境。

## Acceptance Criteria

### 報告產出與內容
- [ ] 已建立一份總結性質的錯誤報告文件（如 `bug_report.md`）。
- [ ] 報告中明確列出了至少 20 個獨立的錯誤項目。
- [ ] 每一個錯誤項目皆包含確切的檔案路徑與行號。
- [ ] 每一個錯誤項目皆包含基於程式碼靜態分析的原因解釋。
- [ ] 每一個錯誤項目皆提供了解決該問題的具體修復建議。

### 系統狀態
- [ ] 專案目錄中的原始程式碼檔案完全沒有被修改。
