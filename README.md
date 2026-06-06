# anki_pi

這是一個基於 Flask 與 FSRS 排程演算法的輕量級記憶卡 (Anki-like) Web 應用程式，專為在樹莓派 (Raspberry Pi) 或 Intranet 環境上運行而設計。它結合了傳統的抽認卡學習與 Discord 的整合，讓學習過程更有效率。

## ✨ 主要功能

- **🧠 間隔重複 (Spaced Repetition):** 內建 [FSRS 演算法](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)，根據作答評分（忘記/困難/普通/簡單）動態安排下次複習時間。
- **📖 字典查詢:**
    - 支援外部字典查詢，可點擊字典圖示前往 Cambridge 字典。
- **🛠️ 資料庫優化 (Merge Duplicates):**
    - 支援匯入時自動合併重複的單字卡片（將新內容串接於舊內容之後）。
- **📚 學習模式:**
    - **傳統模式 (Traditional Mode):** 標準的翻卡式學習，支援兩種記憶策略。
- **📂 方便的卡片管理與瀏覽:**
    - 支援資料夾與牌組管理（牌組可指派到多個資料夾）。
    - **牌組快速瀏覽**：首頁每個牌組旁皆有「瀏覽」按鈕，可一鍵進入卡片管理庫，專屬檢視、關鍵字搜尋與分頁瀏覽該牌組的卡片。
    - 當在特定牌組瀏覽畫面時，點選「新建卡片」或「貼上內容匯入」會自動預設勾選當前牌組。
    - 支援從 CSV 格式「貼上內容」進行批次匯入。
    - 一鍵重置所有學習進度或刪除所有卡片。
- **🛡️ 安全與備份:**
    - **自動備份:** 每次執行更新腳本時，系統會自動備份資料庫至 `backups/` 資料夾。
    - **一鍵還原:** 提供還原腳本 (`restore.sh` / `restore.ps1`)，可隨時將資料庫回復至先前的狀態。
- **🎨 現代化介面:**
    - 簡潔、響應式的網頁設計，適配桌機與行動裝置、要有黑白底切換。

## 🛠️ 技術棧

- **後端:** Python, Flask
- **前端:** 原生 HTML/CSS/JavaScript (無須編譯)
- **資料庫:** SQLite
- **記憶排程:** FSRS (`fsrs` 套件)
- **表單安全:** Flask-WTF + CSRFProtect
- **環境管理:** dotenv (`config.py` 統一管理)

---

## 🚀 快速開始

我們提供了一套自動化腳本，讓你在樹莓派、Linux 或 Windows 系統上輕鬆部署。

### 1. 安裝 (Installation)

#### 🐧 Linux / Raspberry Pi

**前置需求:**
- 樹莓派 OS (Raspberry Pi OS) 或基於 Debian/Ubuntu 的 Linux 系統
- Python 3.x

**步驟:**

1.  **克隆專案:**
    ```bash
    git clone https://github.com/kcy3f0/anki_pi.git
    cd anki_pi
    ```

2.  **執行安裝腳本:**
    *(請使用一般使用者執行，不要加 sudo)*
    ```bash
    ./install.sh
    ```

    安裝過程中，腳本會協助建立 `.env` 設定檔：
    - `SECRET_KEY`: 自動生成。
    - `DISCORD_WEBHOOK_URL`: (選填) 設定 Discord 通知。

3.  **完成!**
    - 服務將自動註冊為 Systemd Service (`anki_pi.service`) 並啟動。
    - 瀏覽器打開 `http://<你的IP>:10000` 即可使用。

#### 🪟 Windows

**前置需求:**
- Windows 10/11
- [Python 3.x](https://www.python.org/downloads/) (安裝時請勾選 "Add Python to PATH")
- [Git for Windows](https://git-scm.com/downloads)

**步驟:**

1.  **克隆專案:**
    在 PowerShell 或 CMD 中執行：
    ```powershell
    cd anki_pi
    ```

2.  **執行安裝腳本:**
    - 在 `anki_pi` 資料夾中找到 `install.ps1`。
    - 右鍵點擊檔案，選擇 **「使用 PowerShell 執行」 (Run with PowerShell)**。
    - 或是直接在 PowerShell 視窗中執行：
        ```powershell
        .\install.ps1
        ```

3.  **設定:**
    - 腳本會自動建立虛擬環境、安裝依賴。
    - 依照提示輸入 `.env` 設定 (SECRET_KEY 會自動生成)。

4.  **完成!**
    - 桌面會建立一個 **Anki Pi** 的捷徑。
    - 雙擊捷徑即可啟動應用程式 (會開啟一個黑色視窗，請勿關閉)。
    - 瀏覽器打開 `http://127.0.0.1:10000` 即可使用。

### 2. 更新 (Update)

當專案有新版本時，請使用更新腳本來確保資料庫與依賴的完整性。

#### 🐧 Linux / Raspberry Pi

```bash
./update.sh
```
此腳本會自動：
1. 備份當前資料庫至 `backups/`。
2. 執行 `git pull` 拉取最新程式碼。
3. 更新 Python 依賴套件。
4. 重新寫入 Systemd 服務設定以確保啟動路徑正確（適用於扁平化結構更新）。
5. 重新啟動服務。

#### 🪟 Windows

1.  關閉正在運行的 Anki Pi 視窗。
2.  右鍵點擊 `update.ps1`，選擇 **「使用 PowerShell 執行」**。
3.  腳本會自動備份資料庫、拉取最新程式碼並更新依賴。
4.  更新完成後，重新使用桌面捷徑啟動即可。

### 3. 還原 (Restore)

若更新後發生問題，或想回溯資料庫狀態：

#### 🐧 Linux / Raspberry Pi
```bash
./restore.sh
```

#### 🪟 Windows
右鍵點擊 `restore.ps1`，選擇 **「使用 PowerShell 執行」**。

系統將列出可用的備份檔供您選擇還原。

---

## 📖 如何使用

### 新增卡片

- **手動新增:**
    - 點擊主畫面的 "✏️ 新增卡片"。
    - 輸入正面 (英文)、背面 (中文)，並選擇卡片類型。
    - **卡片類型說明:**
        - **只要認得 (recognize):** 固定顯示**正面 (英文)**，考驗你是否能回想起中文含義。
        - **需要會拼 (spell):** 隨機顯示正面或背面。若顯示中文 (背面)，則需拼寫出英文 (正面)。

- **批次匯入:**
    - 點擊 "📋 貼上內容匯入"。
    - 直接將 CSV 格式的文字貼入文字框中。
    - 格式範例：
        ```csv
        apple,蘋果
        banana,香蕉
        ```

### 學習

1.  點擊首頁的資料夾或牌組開始學習。
2.  **播放發音:** 點擊 🔊 圖示。
3.  **評分:** 根據記憶程度選擇按鈕，系統將自動計算下次複習時間。

---

## 🤝 貢獻

歡迎提交 Pull Request 或回報問題！

---
## ⚖️ 授權與版權聲明 (License and Attribution)

本專案採用 **GNU Affero General Public License v3.0 (AGPL-3.0) 或更新版本** 進行授權。詳細授權條款請參閱專案中的 [LICENSE](file:///C:/Users/kcy3f/anki_pi/LICENSE) 檔案。

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0) or later**. See the [LICENSE](file:///C:/Users/kcy3f/anki_pi/LICENSE) file for details.

---

### 📌 聲明與致謝 / Disclaimer and Attribution

1. **非官方聲明 / Disclaimer**
   - **中文**：本專案是一個獨立開發、非官方的學習管理工具，受 Anki 專案啟發（Anki-inspired web application），與官方的 Anki 專案（Anki, AnkiWeb, AnkiMobile 或 AnkiDroid）無任何關聯，亦未獲得官方的背書、贊助或授權。
   - **English**: This is an independent, unofficial study management tool inspired by the Anki project (Anki-inspired web application). It is not affiliated with, endorsed, or sponsored by the official Anki project (Anki, AnkiWeb, AnkiMobile, or AnkiDroid).

2. **對原專案的致敬 / Attribution and Acknowledgments**
   - **中文**：本專案的設計概念與排程邏輯深深啟發自開源的 **Anki** 專案。我們在此向原作者及開源社群表達誠摯的感謝。
     - 官方 Anki 專案首頁：[https://apps.ankiweb.net](https://apps.ankiweb.net)
     - 官方 Anki 專案原始碼：[https://github.com/ankitects/anki](https://github.com/ankitects/anki)
   - **English**: The design concepts and scheduling logic of this project are deeply inspired by the open-source **Anki** project. We express our sincere gratitude to the original authors and the open-source community.
     - Anki Webpage: [https://apps.ankiweb.net](https://apps.ankiweb.net)
     - Anki Repository: [https://github.com/ankitects/anki](https://github.com/ankitects/anki)

3. **Anki 商標與標誌 / Anki Trademarks and Logos**
   - **中文**：本專案與官方 Anki 專案無關。若使用 Anki 的 Logo，將完全遵循其授權條款：包含附上指向 [Anki 官網](https://apps.ankiweb.net) 的連結、表明此非官方出版，且未對圖檔本身進行修改。
   - **English**: This project has no affiliation with the official Anki project. Any use of the Anki logo will strictly comply with its trademark terms: providing a link to [https://apps.ankiweb.net](https://apps.ankiweb.net), making it clear that this content is an independent work and not originating from the Anki project, and keeping the logo unmodified.
