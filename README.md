# anki_pi

這是一個基於 Flask 和 SM-2 演算法的輕量級記憶卡 (Anki-like) Web 應用程式，專為在樹莓派 (Raspberry Pi) 或其他低功耗設備上運行而設計。它結合了傳統的抽認卡學習、AI 出題以及與 Discord 的整合，讓學習過程更有效率和趣味。

## ✨ 主要功能

- **🧠 間隔重複 (Spaced Repetition):** 內建 [SM-2 演算法](https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2_algorithm)，根據你的記憶曲線自動安排複習時間。
- **🔊 語音朗讀 (TTS):** 支援 Text-to-Speech，可點擊喇叭圖示聆聽單字或句子發音（使用 Microsoft Edge TTS 或 Google TTS）。
- **📚 學習模式:**
    - **傳統模式:** 標準的翻卡式學習，支援「只要認得」與「需要會拼」兩種卡片類型。
    - **AI 隨堂考:** 在學習過程中，可隨時呼叫 AI (整合 [Ollama](https://ollama.ai/)) 針對當前單字進行生活化造句，或進行隨機出題測驗。
- **📂 方便的卡片管理:**
    - 手動新增單字卡。
    - 支援從 CSV 格式貼上內容批次匯入。
    - 一鍵重置所有學習進度。
- **🔔 Discord 通知:**
    - 每日定時提醒需要複習的卡片數量。
- **🎨 現代化介面:**
    - 簡潔、響應式的網頁設計。
    - 支援淺色/深色模式切換。

## 🛠️ 技術棧

- **後端:** Python, Flask
- **前端:** 原生 HTML/CSS/JavaScript
- **資料庫:** SQLite
- **AI 整合:** Ollama (可接入 Gemma, Llama3, Mistral 等模型)
- **語音:** edge-tts, gTTS
- **通知:** Discord Webhook

---

## 🚀 快速開始

我們提供了一個自動化安裝腳本 `install.sh`，可以幫你一次完成系統更新、依賴安裝、環境設定、服務啟動以及每日提醒排程。

### 1. 環境設定與安裝

**前置需求:**
- 樹莓派 OS (Raspberry Pi OS) 或其他基於 Debian/Ubuntu 的 Linux 系統
- Python 3.x
- 已安裝 Ollama 的伺服器 (可與本應用程式在不同電腦)

**安裝步驟:**

1.  **克隆專案:**
    ```bash
    git clone https://github.com/your-username/anki_pi.git
    cd anki_pi
    ```

2.  **執行安裝腳本:**
    *(請直接執行，不要加 sudo，腳本會在需要時自動請求權限)*
    ```bash
    ./install.sh
    ```

    安裝過程中，腳本會提示你輸入以下資訊：
    - `SECRET_KEY`: 按 Enter 可自動生成隨機密鑰。
    - `OLLAMA_API_URL`: 輸入 Ollama 伺服器的位置 (預設為 `http://127.0.0.1:11434/api/generate`)。
    - `DISCORD_WEBHOOK_URL`: (選填) 輸入你的 Discord Webhook 網址以啟用通知。

3.  **完成!**
    腳本執行完畢後，服務會自動啟動。
    - **訪問應用:** 在瀏覽器中打開 `http://<你的樹莓派IP>:10000`
    - **每日提醒:** 腳本已自動設定每天早上 09:00 執行提醒檢查。

### 手動安裝 (進階使用者)

如果你不想使用自動化腳本，可以參考以下步驟：

1.  建立並啟用 Python 虛擬環境 (`python -m venv venv`, `source venv/bin/activate`)。
2.  安裝依賴 (`pip install -r requirements.txt`)。
3.  複製 `.env.example` 為 `.env` 並填寫設定。
4.  初始化資料庫並啟動 (`python app.py`)。

---

## 📖 如何使用

### 新增卡片

- **手動新增:**
    - 點擊主畫面的 "✏️ 新增卡片"。
    - 輸入正面 (問題)、背面 (答案)，並選擇卡片類型 (`只要認得` 或 `需要會拼`) 後儲存。
    - **卡片類型說明:**
        - **只要認得 (recognize):** 複習時會隨機顯示正面或背面，考驗你是否能辨識。
        - **需要會拼 (spell):** 複習時會強制顯示中文 (背面)，要求你拼寫出英文 (正面)。

- **批次匯入:**
    - 點擊主畫面的 "📋 貼上內容匯入"。
    - 貼上 CSV 格式的內容，每行代表一張卡片。
    - 格式說明：
        - 第一欄是 "正面"，第二欄是 "背面"。
        - 範例：
        ```csv
        apple,蘋果
        banana,香蕉
        cat,貓
        ```

### 學習

- **開始學習:** 點擊首頁的資料夾或牌組即可開始。
- **學習流程:**
    1.  顯示卡片正面 (或背面，視卡片類型與隨機機制而定)。
    2.  可點擊 🔊 播放發音。
    3.  思考答案後，點擊「顯示答案」。
    4.  **AI 輔助:** 在答案頁面，可以點擊「✨ AI 造句」讓 AI 生成例句幫助記憶。
    5.  **評分:** 根據你的記憶程度選擇 "忘記"、"困難"、"普通"、"簡單"，系統將依此安排下次複習時間。

### 每日提醒

`install.sh` 腳本已經自動設定了 crontab。
若需要修改提醒時間，請執行 `crontab -e` 並修改對應的行：
```
0 9 * * * /path/to/your/project/run_reminder.sh >> ...
```

## 🤝 貢獻

歡迎提交 Pull Request 或回報問題！

## 📄 授權

本專案採用 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) 授權](https://creativecommons.org/licenses/by-nc-sa/4.0/)。
請注意，此授權不允許商業用途。
