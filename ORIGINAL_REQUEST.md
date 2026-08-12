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

## Follow-up — 2026-08-12T14:37:42Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Fix all potential bugs in anki_pi without Python runtime

Working directory: c:\Users\kcy3f\anki_pi
Integrity mode: development

## Requirements

### R1. 全面修復已知 26 個 Bugs
根據 `bug_report.md` 紀錄的 26 個問題（涵蓋安全漏洞、SQL 外鍵刪除順序、連線洩漏、FSRS 初始狀態、CSRF 錯誤處理、時區與微秒解析、CSV 解析等），修復 `app.py`、`database.py`、`config.py`、`forms.py` 及相關檔案。

### R2. 靜態分析與二次審查
進行靜態程式碼邏輯審查，確保沒有引入新的語法錯誤或邏輯缺陷，並保持函數簽名與業務邏輯的一致性。

### R3. 更新測試與文件
更新 `test_exam_scheduling.py` 中因 Bug 9 修復（FSRS 初始 state 改為 0）而受影響的斷言與測試數據。

## Acceptance Criteria

### 程式碼修復與驗證
- [ ] `app.py` 任意重導向 (Bug 1) 已修復（使用安全 URL 驗證）。
- [ ] `app.py` CSRF 錯誤處理 (Bug 2 & 11) 已修正為適當快閃提示與跳轉。
- [ ] `app.py` 表單驗證失敗 (Bug 3) 改為 render_template 避免資料遺失。
- [ ] `database.py` 時區與日期解析 (Bug 4, 5, 20) 已更正。
- [ ] `database.py` Discord Webhook (Bug 6) 已改為非阻塞背景 Thread。
- [ ] `database.py` 外鍵順序刪除 (Bug 7, 8) 與孤兒卡片 (Bug 24) 已修復。
- [ ] `database.py` FSRS 初始 State 0 (Bug 9) 已全面修正。
- [ ] `database.py` 連線洩漏 (Bug 12, 17) 與交易原子性/Rollback (Bug 13, 14, 15, 19, 22) 已全數使用 with conn / try...finally 修復。
- [ ] `database.py` Offset-aware/naive datetime 比較 (Bug 16) 已修復。
- [ ] `database.py` CSV 換行 (Bug 21) 已改用 io.StringIO。
- [ ] `database.py` 考試過期重新分配 (Bug 23) 已修正冗餘 break 邏輯。
- [ ] `config.py` 與 `app.py` 安全金鑰與 Debug 模式 (Bug 25, 26) 已修正。
- [ ] `test_exam_scheduling.py` 中的初始 state 斷言已同步更新為 0。

