# Anki_Pi 專案靜態分析與安全審查報告 (Bug Report)

本報告針對 `anki_pi` 專案之原始碼（包含 `app.py`、`database.py`、`config.py`、`forms.py` 及相關測試程式）進行了全面的靜態分析與原始碼安全審查。本審查共識別出 **26 個** 獨立的 Bug 與安全性漏洞。報告中詳細記錄了每個 Bug 的編號與名稱、精確檔案路徑與行號、靜態分析原因解釋，以及具體的修復建議與建議修復之程式碼片段。

---

## 目錄
1. [Bug 1: `app.py` 中的任意重新導向漏洞 (Open Redirect)](#bug-1-apppy-中的任意重新導向漏洞-open-redirect)
2. [Bug 2: 設定頁面中無法抵達的 CSRF 錯誤快閃處理 (Unreachable CSRF Error Handling)](#bug-2-設定頁面中無法抵達的-csrf-錯誤快閃處理-unreachable-csrf-error-handling)
3. [Bug 3: 表單驗證失敗時重導向導致使用者輸入資料遺失 (Data Loss on Form Validation Failure)](#bug-3-表單驗證失敗時重導向導致使用者輸入資料遺失-data-loss-on-form-validation-failure)
4. [Bug 4: 依賴伺服器本地時區的考試時間偏移與提前過期 (Timezone-Dependent Exam Date Shift)](#bug-4-依賴伺服器本地時區的考試時間偏移與提前過期-timezone-dependent-exam-date-shift)
5. [Bug 5: 常見時間格式的資料庫日期解析失效 (Silent Date Parsing Failures for Non-T Formats)](#bug-5-常見時間格式的資料庫日期解析失效-silent-date-parsing-failures-for-non-t-formats)
6. [Bug 6: 同步 Webhook 請求導致 Flask 請求主執行緒效能瓶頸 (Synchronous Webhook Blocking)](#bug-6-同步-webhook-請求導致-flask-請求主執行緒效能瓶頸-synchronous-webhook-blocking)
7. [Bug 7: 刪除資料夾時外鍵約束順序錯誤導致資料庫 IntegrityError 崩潰 (IntegrityError on Folder Deletion)](#bug-7-刪除資料夾時外鍵約束順序錯誤導致資料庫-integrityerror-崩潰-integrityerror-on-folder-deletion)
8. [Bug 8: 刪除牌組時外鍵約束順序錯誤導致資料庫 IntegrityError 崩潰 (IntegrityError on Deck Deletion)](#bug-8-刪除牌組時外鍵約束順序錯誤導致資料庫-integrityerror-崩潰-integrityerror-on-deck-deletion)
9. [Bug 9: 新增單字卡、CSV 匯入與進度重置時設定錯誤的初始狀態違反 FSRS 演算法規範 (FSRS Invalid Initial State)](#bug-9-新增單字卡csv-匯入與進度重置時設定錯誤的初始狀態違反-fsrs-演算法規範-fsrs-invalid-initial-state)
10. [Bug 10: CSV 匯入與表單日期輸入無效時靜默容錯導致資料損壞 (Silent Date Fallback to Current Time)](#bug-10-csv-匯入與表單日期輸入無效時靜默容錯導致資料損壞-silent-date-fallback-to-current-time)
11. [Bug 11: 刪除操作路由的 CSRF 驗證失敗時無任何快閃反饋 (Silent CSRF Failures on Deletion Routes)](#bug-11-刪除操作路由的-csrf-驗證失敗時無任何快閃反饋-silent-csrf-failures-on-deletion-routes)
12. [Bug 12: 查詢函數在異常發生時會導致資料庫連線洩漏 (Connection Leakage on Query Exceptions)](#bug-12-查詢函數在異常發生時會導致資料庫連線洩漏-connection-leakage-on-query-exceptions)
13. [Bug 13: `create_deck` 發生異常時提交部分操作產生孤立牌組 (Partial Commit in `create_deck`)](#bug-13-create_deck-發生異常時提交部分操作產生孤立牌組-partial-commit-in-create_deck)
14. [Bug 14: `add_card` 存在競態條件且缺乏交易保護 (Race Condition in `add_card`)](#bug-14-add_card-存在競態條件且缺乏交易保護-race-condition-in-add_card)
15. [Bug 15: `import_csv_data` 批量匯入缺乏異常回滾與連線洩漏風險 (No Transaction Rollback on CSV Import Exception)](#bug-15-import_csv_data-批量匯入缺乏異常回滾與連線洩漏風險-no-transaction-rollback-on-csv-import-exception)
16. [Bug 16: `submit_card_review` 比較時區感知與 offset-naive Datetime 導致執行期崩潰 (Offset-aware/naive Datetime Comparison Crash)](#bug-16-submit_card_review-比較時區感知與-offset-naive-datetime-導致執行期崩潰-offset-awarenaive-datetime-comparison-crash)
17. [Bug 17: `import_exams_csv` 中危險的連線關閉與重新獲取邏輯及連線洩漏 (Dangerous Connection Re-opening in Loop)](#bug-17-import_exams_csv-中危險的連線關閉與重新獲取邏輯及連線洩漏-dangerous-connection-re-opening-in-loop)
18. [Bug 18: `get_folders_with_decks` 存在嚴重的 N+1 查詢與效能瓶頸 (N+1 Query Bottleneck)](#bug-18-get_folders_with_decks-存在嚴重的-n1-查詢與效能瓶頸-n1-query-bottleneck)
19. [Bug 19: `import_exams_csv` 在迴圈內部頻繁 Commit 導致寫入效能低下 (Frequent Commits in CSV Loop)](#bug-19-import_exams_csv-在迴圈內部頻繁-commit-導致寫入效能低下-frequent-commits-in-csv-loop)
20. [Bug 20: 時區解析微秒截斷錯誤導致時區偏移量被丟棄與時區偏差 (Microsecond & Timezone Discard)](#bug-20-時區解析微秒截斷錯誤導致時區偏移量被丟棄與時區偏差-microsecond--timezone-discard)
21. [Bug 21: CSV 匯入無法處理包含引號換行的多行欄位 (CSV Splitlines Bug)](#bug-21-csv-匯入無法處理包含引號換行的-mutiline-欄位-csv-splitlines-bug)
22. [Bug 22: CSV 匯入缺乏異常捕獲導致 SQL 與解析崩潰 (Unhandled CSV Error)](#bug-22-csv-匯入缺乏異常捕獲導致-sql-與解析崩潰-unhandled-csv-error)
23. [Bug 23: 考試過期重新分配時的 break 導致多個 Deck 遺失重配排程 (Redundant Loop Break in Exam Expiration)](#bug-23-考試過期重新分配時的-break-導致多個-deck-遺失重配排程-redundant-loop-break-in-exam-expiration)
24. [Bug 24: 刪除牌組時未處理孤兒卡片造成資料庫殘留垃圾資料 (Orphaned Cards Leak on Delete Deck)](#bug-24-刪除牌組時未處理孤兒卡片造成資料庫殘留垃圾資料-orphaned-cards-leak-on-delete-deck)
25. [Bug 25: 預設寫死且不安全的 `SECRET_KEY` (Hardcoded Security Key)](#bug-25-預設寫死且不安全的-secret_key-hardcoded-security-key)
26. [Bug 26: 於生產/預設環境下以 `debug=True` 運行 Flask 應用程式 (Flask App Run in Debug Mode)](#bug-26-於生產預設環境下以-debugtrue-運行-flask-應用程式-flask-app-run-in-debug-mode)

---

### Bug 1: `app.py` 中的任意重新導向漏洞 (Open Redirect)
* **檔案路徑與精確行號**：`app.py` 第 186 行與第 233 行
* **靜態分析原因解釋**：
  在 `add_card` 及 `import_csv` 路由中，代碼執行完成後會調用 `redirect(request.referrer or url_for('cards_list'))`。`request.referrer` 來自客戶端發送的 HTTP 請求中的 `Referer` 標頭。攻擊者可以通過偽造 `Referer` 標頭或引導用戶點擊包含惡意外部網址的連結，將用戶重導向至釣魚網站或其他惡意站點，此處缺乏對目標網址網域之安全驗證。
* **具體修復建議與建議修復的程式碼片段**：
  引入 `urlparse` 與 `urljoin`，並實作 `is_safe_url` 輔助函數來驗證跳轉目標是否與當前主機網域相同：
  ```python
  from urllib.parse import urlparse, urljoin

  def is_safe_url(target):
      ref_url = urlparse(request.host_url)
      test_url = urlparse(urljoin(request.host_url, target))
      return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

  # 於 app.py 第 186 行與第 233 行修改為：
  referrer = request.referrer
  if referrer and is_safe_url(referrer):
      return redirect(referrer)
  return redirect(url_for('cards_list'))
  ```

---

### Bug 2: 設定頁面中無法抵達的 CSRF 錯誤快閃處理 (Unreachable CSRF Error Handling)
* **檔案路徑與精確行號**：`app.py` 第 327-340 行
* **靜態分析原因解釋**：
  在此專案中，全域啟用了 `CSRFProtect(app)`。該保護器會在 Flask 的 `before_request` 階段自動驗證所有 POST 請求。如果請求中缺少 CSRF Token 或 Token 無效，會直接拋出 `CSRFError`，回傳 400 Bad Request，並中慢請求分發。這導致 `settings` 路由中 `if form.validate_on_submit():` 的 `else` 區塊（試圖 flash `CSRF 驗證失敗`）永遠無法被觸發，形成了死碼（Dead Code），使用者亦會遭遇粗糙的 400 錯誤頁面。
* **具體修復建議與建議修復的程式碼片段**：
  在 Flask 應用程式中註冊一個全域的 `CSRFError` 異常處理器，以快閃（flash）提示使用者，並重新導向至原頁面：
  ```python
  from flask_wtf.csrf import CSRFError

  @app.errorhandler(CSRFError)
  def handle_csrf_error(e):
      flash('CSRF 驗證失敗，請重試或重新整理頁面。', 'danger')
      return redirect(request.referrer or url_for('index'))
  ```

---

### Bug 3: 表單驗證失敗時重導向導致使用者輸入資料遺失 (Data Loss on Form Validation Failure)
* **檔案路徑與精確行號**：
  * `app.py` 第 57-67 行 (`add_folder`)
  * `app.py` 第 77-90 行 (`add_deck`)
  * `app.py` 第 170-186 行 (`add_card`)
  * `app.py` 第 220-233 行 (`import_csv`)
  * `app.py` 第 391-416 行 (`add_exam`)
  * `app.py` 第 418-431 行 (`import_exams`)
* **靜態分析原因解釋**：
  當表單驗證失敗時（如必填欄位空白），程式碼會調用 `flash` 記錄錯誤訊息，然後回傳 `redirect(request.referrer ...)`。這會使瀏覽器發起全新的 GET 請求，重新載入該表單頁面。此時，使用者之前辛苦輸入的未保存資料（例如長篇單字解釋、匯入的 CSV 文字等）將會被完全清空，嚴重損害使用者體驗。
* **具體修復建議與建議修復的程式碼片段**：
  驗證失敗時，不要進行 `redirect`，而是直接渲染原始範本（`render_template`），並將帶有錯誤與原有輸入值的 `form` 物件傳回前端渲染：
  ```python
  # 以 add_card 路由為例（修改 app.py 第 182-186 行）：
  # 代替 return redirect(...)
  # 直接執行獲取上下文資料並渲染範本：
  search = request.args.get('search', '')
  page = request.args.get('page', 1, type=int)
  deck_id = request.args.get('deck_id', None, type=int)
  limit = 20
  cards, total = db.get_all_cards_paged(search, page, limit, deck_id)
  total_pages = (total + limit - 1) // limit
  import_form = ImportForm()
  import_form.decks.choices = form.decks.choices
  
  return render_template(
      'cards.html',
      cards=cards,
      search=search,
      page=page,
      total_pages=total_pages,
      total=total,
      card_form=form,  # 傳回帶有使用者輸入與錯誤的 form
      import_form=import_form,
      deck_id=deck_id,
      current_deck=None
  )
  ```

---

### Bug 4: 依賴伺服器本地時區的考試時間偏移與提前過期 (Timezone-Dependent Exam Date Shift)
* **檔案路徑與精確行號**：`database.py` 第 706-712 行 (被 `app.py` 第 405 行與第 422 行呼叫)
* **靜態分析原因解釋**：
  在 `parse_input_datetime` 中，程式碼調用了不帶參數的 `dt.astimezone()`。這會將時間轉換為執行此專案的伺服器本地時區。隨後將時間歸零為本地時區的午夜 `00:00:00`，最後再轉換回 UTC 時區儲存。
  這會產生嚴重的時區偏移問題。例如，在 UTC+8（台北時間）環境下，輸入 `2026-06-15`，轉換後在本地歸零為 `2026-06-15 00:00:00+08:00`，再存入資料庫時會變成 UTC 的 `2026-06-14 16:00:00`。這會導致此考試在 UTC 時間的 6 月 14 日 16:00 (台北時間 15 日 00:00) 即被判定為過期，使排程上限防禦機制提早一天失效。
* **具體修復建議與建議修復的程式碼片段**：
  避免使用本地時區進行日期轉換，統一在 UTC 時區下進行日期的獲取與時間歸零：
  ```python
  def parse_input_datetime(date_str):
      # ... 解析日期字串為 dt ...
      if dt.tzinfo is None:
          dt = dt.replace(tzinfo=timezone.utc)
      # 統一在 UTC 歸零為午夜，或設置為該日的 23:59:59 以防止提前判定過期
      utc_dt = dt.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
      return utc_dt
  ```

---

### Bug 5: 常見時間格式的資料庫日期解析失效 (Silent Date Parsing Failures for Non-T Formats)
* **檔案路徑與精確行號**：`database.py` 第 17-51 行
* **靜態分析原因解釋**：
  在 `parse_db_datetime` 中，程式碼先判斷字串中是否含有 `'T'`。若無 `'T'`（即不包含 ISO 8601 分隔符，如常見的資料庫日期時間格式 `YYYY-MM-DD HH:MM:SS`），會直接進入 `else` 分支。該分支僅使用 `strptime(dt_str, "%Y-%m-%d")` 嘗試解析日期。如果字串中含有時間部分，解析將會拋出 `ValueError` 並返回 `None`。
  這會導致從 SQLite 中讀取到的複習卡片時間 `next_review` parsed 失敗為 `None`。此時卡片的到期比對 `next_review <= now` 永遠不成立，導致卡片被無限期擱置，無法再出現於使用者的複習佇列中。
* **具體修復建議與建議修復的程式碼片段**：
  在 `else` 分支中增加對常見無 `'T'` 格式帶時間字串的解析嘗試：
  ```python
  # 修改 database.py 第 46-51 行：
  else:
      for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
          try:
              return datetime.strptime(dt_str, fmt).replace(tzinfo=timezone.utc)
          except ValueError:
              continue
      return None
  ```

---

### Bug 6: 同步 Webhook 請求導致 Flask 請求主執行緒效能瓶頸 (Synchronous Webhook Blocking)
* **檔案路徑與精確行號**：`database.py` 第 58-65 行
* **靜態分析原因解釋**：
  `send_discord_message` 函數使用 `requests.post` 同步向 Discord 發送網路請求，並設置了 5 秒的超時。在單字卡複習提交 (`submit_card_review`)、匯入卡片與進度重設等路由中，後端必須等待該 Webhook 的 HTTP 回應，才會把結果回傳給使用者。在網路不穩定或 Discord 伺服器延遲時，會直接卡死 Flask 主執行緒長達 5 秒，使用者介面隨之凍結。
* **具體修復建議與建議修復的程式碼片段**：
  利用 Python `threading` 套件將 Webhook 的發送動作移至背景執行緒異步執行，避免阻塞主請求執行緒：
  ```python
  import threading

  def send_discord_message(content):
      url = Config.DISCORD_WEBHOOK_URL
      if not url:
          return
      
      def run_send():
          try:
              requests.post(url, json={"content": content}, timeout=5)
          except Exception as e:
              print(f"Error sending Discord Webhook: {e}")
              
      threading.Thread(target=run_send, daemon=True).start()
  ```

---

### Bug 7: 刪除資料夾時外鍵約束順序錯誤導致資料庫 IntegrityError 崩潰 (IntegrityError on Folder Deletion)
* **檔案路徑與精確行號**：`database.py` 第 167-172 行
* **靜態分析原因解釋**：
  當系統啟用了 SQLite 外鍵約束 (`PRAGMA foreign_keys = ON;`) 時，若直接刪除父資料表（`folders`）的記錄，而子資料表（`deck_folders`）中仍有參照該資料夾 `folder_id` 的外鍵記錄，且未配置 `ON DELETE CASCADE`，資料庫會立即拋出 `sqlite3.IntegrityError: FOREIGN KEY constraint failed` 外鍵違反約束錯誤，導致應用程式執行期崩潰。此處程式碼在刪除子表記錄前，試圖先刪除父表記錄。
* **具體修復建議與建議修復的程式碼片段**：
  先刪除子資料表（`deck_folders`）中的關聯，再刪除父資料表（`folders`）中的主記錄：
  ```python
  def delete_folder(folder_id):
      conn = get_db_connection()
      try:
          with conn:
              conn.execute("DELETE FROM deck_folders WHERE folder_id = ?", (folder_id,))
              conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
      finally:
          conn.close()
  ```

---

### Bug 8: 刪除牌組時外鍵約束順序錯誤導致資料庫 IntegrityError 崩潰 (IntegrityError on Deck Deletion)
* **檔案路徑與精確行號**：`database.py` 第 202-208 行
* **靜態分析原因解釋**：
  如同 Bug 7，此處在 `delete_deck` 函數中，先對父表 `decks` 執行了 `DELETE`，才去對關聯子表 `deck_folders` 與 `card_decks` 執行 `DELETE`。啟用外鍵約束時，這會立即觸發 `sqlite3.IntegrityError` 並導致系統崩潰。
* **具體修復建議與建議修復的程式碼片段**：
  調整 SQL 執行順序，先清除所有子表記錄，再行刪除主表記錄：
  ```python
  def delete_deck(deck_id):
      conn = get_db_connection()
      try:
          with conn:
              conn.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
              conn.execute("DELETE FROM card_decks WHERE deck_id = ?", (deck_id,))
              conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
      finally:
          conn.close()
  ```

---

### Bug 9: 新增單字卡、CSV 匯入與進度重置時設定錯誤的初始狀態違反 FSRS 演算法規範 (FSRS Invalid Initial State)
* **檔案路徑與精確行號**：
  * `database.py` 第 313 行 (`add_card`)
  * `database.py` 第 387 行 (`import_csv_data` 處的 INSERT)
  * `database.py` 第 645 行 (`reset_all_learning_progress` 處 the UPDATE)
  * `test_exam_scheduling.py` 第 26, 164, 321, 378, 386 行
* **靜態分析原因解釋**：
  在 FSRS 演算法規範中，全新或重置的卡片在首次複習前，其狀態（`state`）應被記錄為 `0` (代表 `State.New`)。然而，此專案在新增、匯入或重設卡片時，將其初始 `state` 強制設定為 `1` (代表 `State.Learning`)，此時卡片的複習次數（`reps`）為 0，且 `stability` 與 `difficulty` 均為空值 (`NULL`)。
  當使用者隨後點擊評級進行複習時，FSRS 調度器加載該卡片。因為 state 是 `Learning` (1) 且 `stability` 為 `None`，FSRS 將直接跳過 New 狀態的初始計算邏輯，並在進行乘法等數學運算時拋出 `TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'` 執行期崩潰。
* **具體修復建議與建議修復的程式碼片段**：
  將所有新建立卡片及重設卡片時的預設狀態從 `1` 改為 `0`：
  ```python
  # database.py 第 313 行與第 387 行：
  # 將 VALUES 中的 1 改為 0：
  cur.execute("""
      INSERT INTO cards (front, back, next_review, state, step, stability, difficulty, last_review, reps, lapses, card_type)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """, (front, back, now_str, 0, 0, None, None, None, 0, 0, card_type))

  # database.py 第 645 行：
  # 將 UPDATE 中的 state = 1 改為 state = 0：
  conn.execute("""
      UPDATE cards
      SET state = 0, step = 0, stability = NULL, difficulty = NULL, last_review = NULL, next_review = ?, reps = 0, lapses = 0
  """)
  ```

---

### Bug 10: CSV 匯入與表單日期輸入無效時靜默容錯導致資料損壞 (Silent Date Fallback to Current Time)
* **檔案路徑與精確行號**：`database.py` 第 703-704 行 (於 `parse_input_datetime` 中)
* **靜態分析原因解釋**：
  在 `parse_input_datetime` 解析考試日期時，如果遇到無法解析的日期時間格式，最底層的異常捕獲分支會執行 `dt = datetime.now()`，將無效的日期靜默轉換為目前系統時間，且不給予使用者任何錯誤警告。這會導致使用者設定或 CSV 中填錯的考試日期被寫入為「今天」，引發資料損壞，且讓使用者誤以為匯入完全成功。
* **具體修復建議與建議修復的程式碼片段**：
  不進行靜默容錯，而是拋出 `ValueError` 異常，讓上層路由能夠捕獲該錯誤，中斷匯入，並向使用者回報具體錯誤：
  ```python
  # 修改 database.py 第 703-704 行：
  except Exception:
      raise ValueError(f"無法解析日期格式，請使用 ISO (YYYY-MM-DD) 格式。輸入值：{date_str}")
  ```

---

### Bug 11: 刪除操作路由的 CSRF 驗證失敗時無任何快閃反饋 (Silent CSRF Failures on Deletion Routes)
* **檔案路徑與精確行號**：`app.py` 第 69-75 行 (`delete_folder`), 第 118-124 行 (`delete_deck`), 第 212-218 行 (`delete_card`), 第 433-439 行 (`delete_exam`)
* **靜態分析原因解釋**：
  這些刪除路由均採用 POST 方式送出並在內部使用 `form.validate_on_submit()` 來檢驗 CSRF Token。然而，當 Token 過期、遺失或 CSRF 驗證失敗時，`validate_on_submit` 返回 `False`。路由程式碼直接默默地跳轉（redirect），沒有在 `else` 分支做任何快閃錯誤反饋。這會導致使用者在前端點選刪除時頁面重新整理卻什麼都沒發生（項目依然存在），使用者亦無從得知是由於安全憑證失效所致。
* **具體修復建議與建議修復的程式碼片段**：
  在 `form.validate_on_submit()` 後面增加 `else` 分支，向使用者發送快閃警告提示：
  ```python
  # 以 delete_folder 為例修改 app.py：
  @app.route('/folders/delete/<int:folder_id>', methods=['POST'])
  def delete_folder(folder_id):
      form = EmptyForm()
      if form.validate_on_submit():
          db.delete_folder(folder_id)
          flash('資料夾已刪除！', 'warning')
      else:
          flash('刪除失敗：CSRF 憑證無效或已過期，請重新整理頁面再試。', 'danger')
      return redirect(url_for('index'))
  ```

---

### Bug 12: 查詢函數在異常發生時會導致資料庫連線洩漏 (Connection Leakage on Query Exceptions)
* **檔案路徑與精確行號**：`database.py` (第 69-73 行、第 75-79 行、第 210-214 行、第 271-281 行、第 666-672 行等多處)
* **靜態分析原因解釋**：
  在許多查詢函數中，程式碼在開頭獲取連線 `conn = get_db_connection()` 後，直接執行 SQL 查詢，並在結尾調用 `conn.close()`。如果在 SQL 執行期間拋出任何異常（例如資料表被鎖定、資料庫唯讀或損壞），函數會直接中斷並往上拋出異常，使得底下的 `conn.close()` 被跳過。這會導致資料庫連線洩漏，在長時間運行的 Flask 應用程式中會耗盡伺服器的檔案描述符，進而使資料庫鎖定或伺服器崩潰。
* **具體修復建議與建議修復的程式碼片段**：
  使用 `try...finally` 語句或 `contextlib.closing` 語意管理器，確保不論是否拋出異常，連線均能被正確關閉：
  ```python
  # 以 get_all_folders 為例：
  def get_all_folders():
      conn = get_db_connection()
      try:
          return conn.execute("SELECT * FROM folders").fetchall()
      finally:
          conn.close()
  ```

---

### Bug 13: `create_deck` 發生異常時提交部分操作產生孤立牌組 (Partial Commit in `create_deck`)
* **檔案路徑與精確行號**：`database.py` 第 174-189 行
* **靜態分析原因解釋**：
  在 `create_deck(name, folder_ids=None)` 中，程式碼首先向 `decks` 寫入一條記錄，並在第 179 行立即調用了 `conn.commit()` 提交寫入。如果此時傳入了 `folder_ids`，但在隨後對關係資料表 `deck_folders` 執行 `INSERT` 時因為某些原因（如資料夾 ID 不存在觸發外鍵錯誤）拋出異常，程式會跳出並在 `finally` 關閉連線。這導致 `decks` 的寫入已經永久生效，而與資料夾的關聯卻完全失敗，從而在資料庫中產生了不屬於任何資料夾的「孤立牌組」，破壞了業務交易的原子性（Atomicity）。
* **具體修復建議與建議修復的程式碼片段**：
  移除中間提交，將整個建立與關聯流程包裹在一個事務中，僅在全部成功時提交：
  ```python
  def create_deck(name, folder_ids=None):
      conn = get_db_connection()
      try:
          with conn:  # with conn 自動在區塊結束時 commit，出錯時 rollback
              cur = conn.cursor()
              cur.execute("INSERT INTO decks (name) VALUES (?)", (name,))
              deck_id = cur.lastrowid
              
              if folder_ids:
                  for fid in folder_ids:
                      cur.execute("INSERT INTO deck_folders (deck_id, folder_id) VALUES (?, ?)", (deck_id, fid))
              return deck_id
      finally:
          conn.close()
  ```

---

### Bug 14: `add_card` 存在競態條件且缺乏交易保護 (Race Condition in `add_card`)
* **檔案路徑與精確行號**：`database.py` 第 283-324 行
* **靜態分析原因解釋**：
  `add_card` 採用了「先檢查再執行」模式。它先執行 `SELECT * FROM cards WHERE front = ?`。如果在高併發環境下，兩個請求同時對相同單字發起 `add_card`，兩者都會查到 `existing` 為空，進而同時執行 `INSERT`，導致資料庫中產生重複的單字卡記錄。此外，若在插入卡片後、寫入 `card_decks` 關係表時發生錯誤，先前已寫入的卡片將無法回滾，產生髒資料。
* **具體修復建議與建議修復的程式碼片段**：
  使用交易（Transaction）包裹整個檢查與寫入區塊，並在資料庫層級的 `cards` 表對 `front` 欄位建立唯一索引（UNIQUE Constraint）：
  ```python
  def add_card(front, back, card_type, deck_ids):
      conn = get_db_connection()
      try:
          with conn:
              cur = conn.cursor()
              front = front.strip()
              back = back.strip()
              
              existing = cur.execute("SELECT * FROM cards WHERE front = ?", (front,)).fetchone()
              if existing:
                  # 合併釋義邏輯...
                  cur.execute("UPDATE cards SET back = ?, card_type = ? WHERE id = ?", ...)
                  card_id = existing['id']
                  merged = True
              else:
                  now_str = format_datetime_for_db(datetime.now(timezone.utc))
                  cur.execute("INSERT INTO cards ... VALUES (?, ?, ...)", (front, back, now_str, 0, ...))
                  card_id = cur.lastrowid
                  merged = False
                  
              for did in deck_ids:
                  cur.execute("INSERT INTO card_decks (card_id, deck_id) VALUES (?, ?)", (card_id, did))
                  
              return card_id, merged
      finally:
          conn.close()
  ```

---

### Bug 15: `import_csv_data` 批量匯入缺乏異常回滾與連線洩漏風險 (No Transaction Rollback on CSV Import Exception)
* **檔案路徑與精確行號**：`database.py` 第 352-398 行
* **靜態分析原因解釋**：
  在 `import_csv_data` 函數中，代碼會開闢一個連線並遍歷 CSV 每一行。只有在全部迴圈結束後才在第 397 行調用 `conn.commit()`。若中途某一行因為 SQLite 約束衝突（如外鍵約束失敗）拋出異常，函數將直接中斷，使得最後的 `conn.commit()` 與 `conn.close()` 均無法執行。這不僅會造成資料庫連線洩漏，也會使先前成功的寫入操作在資料庫中處於未決的事務掛起狀態，進而鎖定資料庫。
* **具體修復建議與建議修復的程式碼片段**：
  使用 `with conn:` 語意管理器自動處理事務的提交與回滾，並在 `finally` 中安全關閉連線：
  ```python
  def import_csv_data(csv_text, deck_ids, card_type="recognize"):
      conn = get_db_connection()
      try:
          with conn:
              cur = conn.cursor()
              # CSV 解析與遍歷寫入...
              # 遍歷完畢後無須手動 commit，with conn 會自動處理
      finally:
          conn.close()
  ```

---

### Bug 16: `submit_card_review` 比較時區感知與 offset-naive Datetime 導致執行期崩潰 (Offset-aware/naive Datetime Comparison Crash)
* **檔案路徑與精確行號**：`database.py` 第 590-596 行
* **靜態分析原因解釋**：
  在 `submit_card_review` 中，`earliest_exam_date` 經由 `parse_db_datetime` 解析後，返回一個帶有 UTC 時區的 offset-aware `datetime` 對象。而 `adjusted_due` 是由 FSRS 庫計算產出的。如果該 FSRS 物件的 `due` 屬性是不帶時區資訊的 offset-naive `datetime` 物件，在進行 `adjusted_due >= earliest_exam_date` 比較時，Python 會直接拋出 `TypeError: can't compare offset-naive and offset-aware datetimes`，導致整個複習提交功能崩潰。
* **具體修復建議與建議修復的程式碼片段**：
  在進行比較之前，檢測並確保 `adjusted_due` 具有 UTC 時區資訊：
  ```python
  # 修改 database.py 第 590-593 行：
  if earliest_exam_row and earliest_exam_row[0]:
      earliest_exam_date = parse_db_datetime(earliest_exam_row[0])
      if adjusted_due.tzinfo is None:
          adjusted_due = adjusted_due.replace(tzinfo=timezone.utc)
      if adjusted_due >= earliest_exam_date:
          capped_due = earliest_exam_date - timedelta(days=1)
  ```

---

### Bug 17: `import_exams_csv` 中危險的連線關閉與重新獲取邏輯及連線洩漏 (Dangerous Connection Re-opening in Loop)
* **檔案路徑與精確行號**：`database.py` 第 1046-1052 行
* **靜態分析原因解釋**：
  在 `import_exams_csv` 中，如果導入的考試數量大於 0，會先獲取一個新連線 `conn`。然後在 `unprocessed` 的迴圈內部，程式碼先調用 `conn.close()` 關閉連線，隨後調用 `distribute_exam_cards(r['id'])`（此函式內部會自行開關一次連線），接著又調用 `conn = get_db_connection()` 重新獲取連線。
  這種在迴圈內部頻繁關閉並重新建立連線的做法非常危險。在高併發或多執行緒環境下會引發嚴重的 Race Condition 且增加資料庫鎖定（Deadlock）機率。此外，若開頭的 `conn.execute()` 執行失敗，該連線將會洩漏。
* **具體修復建議與建議修復的程式碼片段**：
  重構 `distribute_exam_cards` 使其可以接受一個可傳遞的連線參數 `conn`；在外部呼叫端，保持同一個資料庫連線不中斷，避免在迴圈內反覆關閉重開：
  ```python
  # 重構 distribute_exam_cards 以接受傳遞的 conn
  # 在 import_exams_csv 中修復為：
  if imported_count > 0:
      conn = get_db_connection()
      try:
          unprocessed = conn.execute("SELECT id FROM exams WHERE processed = 0").fetchall()
          for r in unprocessed:
              distribute_exam_cards(r['id'], conn=conn)  # 傳入共用連線，不關閉
      finally:
          conn.close()
  ```

---

### Bug 18: `get_folders_with_decks` 存在嚴重的 N+1 查詢與效能瓶頸 (N+1 Query Bottleneck)
* **檔案路徑與精確行號**：`database.py` 第 81-124 行
* **靜態分析原因解釋**：
  該函數首先執行查詢獲取所有 folders（1 次）。接著，對每個 folder 執行一次查詢來獲取其對應的 decks（N 次）。接著，對每個 deck 呼叫 `get_deck_card_stats`，其中又執行了一次 SQL 查詢來獲取卡片狀態（N * M 次）。
  這會導致嚴重的 N+1 查詢效能瓶頸，如果系統有 20 個資料夾，每個資料夾有 5 個牌組，則需要執行 $1 + 20 + 100 = 121$ 次資料庫查詢！在低功耗硬體（如 Raspberry Pi）上會產生巨大的 I/O 延遲，導致首頁載入極其卡頓。
* **具體修復建議與建議修復的程式碼片段**：
  利用 SQL 的 `LEFT JOIN` 與 `GROUP BY` 進行條件聚合，在一次查詢中取得所有資料夾、牌組與卡片統計：
  ```python
  # 建議使用多表 JOIN 一次性查出統計，例如：
  # SELECT f.id, f.name, d.id, d.name, COUNT(c.id) FILTER (WHERE c.state = 0) AS new_cards...
  # FROM folders f 
  # LEFT JOIN deck_folders df ON f.id = df.folder_id
  # LEFT JOIN decks d ON df.deck_id = d.id
  # LEFT JOIN card_decks cd ON d.id = cd.deck_id
  # LEFT JOIN cards c ON cd.card_id = c.id
  # GROUP BY f.id, d.id
  ```

---

### Bug 19: `import_exams_csv` 在迴圈內部頻繁 Commit 導致寫入效能低下 (Frequent Commits in CSV Loop)
* **檔案路徑與精確行號**：`database.py` 第 985-1043 行
* **靜態分析原因解釋**：
  該函數在解析 CSV 的迴圈中，每處理完一行資料就呼叫一次 `conn.commit()`。在 SQLite 中，每次 commit 都會強制發起實體硬碟的同步寫入（fsync），這是代價極高的磁碟 I/O 操作。如果 CSV 檔案包含數百條考試記錄，這會使導入操作執行長達數十秒。
* **具體修復建議與建議修復的程式碼片段**：
  移除迴圈內部的 `conn.commit()`，將其移到整個 `for` 迴圈外部，使所有數據在單次交易（Transaction）中一起 commit，提升上百倍的寫入效能：
  ```python
  # 修改 database.py
  # 移除 1040 行的 conn.commit()
  for row in reader:
      # ... 處理與插入 ...
  conn.commit()  # 移到 for 迴圈結束後執行
  ```

---

### Bug 20: 時區解析微秒截斷錯誤導致時區偏移量被丟棄與時區偏差 (Microsecond & Timezone Discard)
* **檔案路徑與精確行號**：`database.py` 第 30-34 行（於 `parse_db_datetime` 中）
* **靜態分析原因解釋**：
  在 `parse_db_datetime` 處理含有小數秒（微秒）的時間字串時，代碼使用了 `dt_str.split('.')`。若字串中包含時區偏移量（例如 `2026-06-14T08:01:25.123456+08:00`），`split` 會將其切分為：
  * `base` = `"2026-06-14T08:01:25"`
  * `micro` = `"123456+08:00"`
  
  接著執行 `micro = micro[:6]`，截取前 6 位得到 `"123456"`，此動作將時區偏移量 `+08:00` 完全丟棄。隨後使用 `.replace(tzinfo=timezone.utc)`，將該時間無條件當作 UTC 時間。這導致原本的本地時間與 UTC 產生了 8 小時的巨大偏差，引發排程時間混亂。
* **具體修復建議與建議修復的程式碼片段**：
  使用正規表示式匹配並提取時區部分，在截斷微秒後將時區補回或進行轉換：
  ```python
  import re

  def parse_db_datetime(dt_str):
      if not dt_str:
          return None
      dt_str = dt_str.strip()
      
      # 匹配末尾時區 (如 +08:00, -05:00, Z)
      tz_match = re.search(r'([+-]\d{2}:?\d{2}|Z)$', dt_str)
      tz_part = tz_match.group(1) if tz_match else ""
      if tz_part:
          dt_str = dt_str[:-len(tz_part)]
      
      if '.' in dt_str:
          base, micro = dt_str.split('.')
          micro = micro[:6]
          dt_str = f"{base}.{micro}"
      
      try:
          dt = datetime.fromisoformat(dt_str)
          if tz_part == 'Z' or tz_part == '+00:00' or not tz_part:
              return dt.replace(tzinfo=timezone.utc)
          else:
              # 解析偏移時區並轉為 UTC
              tz_info = datetime.fromisoformat(f"2020-01-01T00:00:00{tz_part}").tzinfo
              return dt.replace(tzinfo=tz_info).astimezone(timezone.utc)
      except ValueError:
          # fallback ...
          try:
              return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
          except ValueError:
              return None
  ```

---

### Bug 21: CSV 匯入無法處理包含引號換行的多行欄位 (CSV Splitlines Bug)
* **檔案路徑與精確行號**：`database.py` 第 356 行與第 982 行
* **靜態分析原因解釋**：
  在導入 CSV 卡片或考試時，程式碼使用 `csv.reader(csv_text.strip().splitlines())`。這會先按換行符號將整個 CSV 切割成字串陣列。
  然而，標準 CSV 格式允許在雙引號包裹的欄位內包含換行符號（例如單字卡背面的中文解釋可能有多行）。使用 `splitlines()` 會強制在引號內的換行符處將欄位截斷，將其拆分成多行獨立資料，導致 `csv.reader` 解析出錯誤的欄位數，造成匯入失敗或欄位內容嚴重錯亂。
* **具體修復建議與建議修復的程式碼片段**：
  應使用 `io.StringIO` 將 CSV 字串封裝為檔案類型的物件後，再直接傳給 `csv.reader` 進行解析：
  ```python
  import io

  # 修改 database.py 第 356 行與第 982 行：
  reader = csv.reader(io.StringIO(csv_text.strip()))
  ```

---

### Bug 22: CSV 匯入缺乏異常捕獲導致 SQL 與解析崩潰 (Unhandled CSV Error)
* **檔案路徑與精確行號**：`database.py` 第 352-405 行與第 978-1056 行
* **靜態分析原因解釋**：
  在遍歷 `reader` 的過程中，程式碼沒有使用 `try...except` 包裹單行處理。如果使用者貼入的 CSV 格式有嚴重錯誤（如引號未成對出現引發 `csv.Error`），或某些行缺失了必填的欄位（如存取欄位 index 超限），程式會直接拋出異常崩潰，導致 Flask 回傳 500 Internal Server Error，且先前已成功寫入的部分資料亦無法回滾。
* **具體修復建議與建議修復的程式碼片段**：
  在讀取每一行時加入 `try...except` 處理，並將整個操作置於交易中，若拋出嚴重錯誤則回滾交易：
  ```python
  def import_csv_data(csv_text, deck_ids, card_type="recognize"):
      conn = get_db_connection()
      try:
          with conn:
              cur = conn.cursor()
              # ...
              for row in reader:
                  try:
                      if not row or len(row) < 2:
                          continue
                      front = row[0].strip()
                      back = row[1].strip()
                      # ...
                  except IndexError:
                      raise ValueError("CSV 檔案中有些行缺少必要的欄位！")
      except csv.Error as e:
          raise ValueError(f"CSV 格式解析失敗：{str(e)}")
      finally:
          conn.close()
  ```

---

### Bug 23: 考試過期重新分配時的 break 導致多個 Deck 遺失重配排程 (Redundant Loop Break in Exam Expiration)
* **檔案路徑與精確行號**：`database.py` 第 838-859 行
* **靜態分析原因解釋**：
  在 `process_expired_exams` 中，當某個擁有多個關聯牌組（Deck 1, Deck 2）的考試過期時，系統需要找出後續受影響的下一個未過期考試以重新調配單字排程。
  在此邏輯中，代碼會按日期排序尋找下一個未過期考試 `u_row`。一旦發現該未過期考試與已過期的牌組集合有任何交集，就會對該未過期考試呼叫 `distribute_exam_cards(u_id)`，接著執行 `break` 終止整個對未過期考試的迭代！
  這會產生一個邏輯漏洞：如果已過期的牌組包含 Deck 1 與 Deck 2，下一個未過期考試 A 僅包含 Deck 1，系統對 A 進行重新分配並 `break` 後，另一個同樣需要被重新調配、包含 Deck 2 的下一個未過期考試 B 將會被完全忽略！導致 Deck 2 的卡片無法被正確地重新分配到考試 B 的排程中。
* **具體修復建議與建議修復的程式碼片段**：
  不應直接使用 `break`，而是應該跟蹤哪些過期的 deck 已被下一個考試覆蓋。只有當所有過期的 deck 都被重新配額，或者沒有更多未過期的考試時，才退出循環。
  ```python
  remaining_decks = set(expired_deck_ids)
  upcoming = cur.execute("SELECT id FROM exams WHERE date > ? AND processed = 0 ORDER BY date ASC", (now_str,)).fetchall()
  for u_row in upcoming:
      if not remaining_decks:
          break
      # 獲取 u_deck_ids ...
      overlap = [d for d in u_deck_ids if d in remaining_decks]
      if overlap:
          conn.close()
          try:
              distribute_exam_cards(u_id)
          finally:
              conn = get_db_connection()
              cur = conn.cursor()
          # 移除已經被重新配額的 decks
          for d in overlap:
              remaining_decks.remove(d)
  ```

---

### Bug 24: 刪除牌組時未處理孤兒卡片造成資料庫殘留垃圾資料 (Orphaned Cards Leak on Delete Deck)
* **檔案路徑與精確行號**：`database.py` 第 202-208 行
* **靜態分析原因解釋**：
  當刪除一個牌組時，該牌組與卡片的關係連結在 `card_decks` 中被刪除，但屬於該牌組的卡片本身仍留在 `cards` 資料表中。
  如果這些卡片僅屬於這一個被刪除的牌組，它們會變成沒有任何關聯牌組的「孤兒卡片」。由於系統中所有的學習佇列與統計數據都是基於 `card_decks` 與牌組進行查詢，這些卡片將永遠無法再被使用者複習或訪問，但在資料庫中卻依然存在，造成垃圾數據累積。
* **具體修復建議與建議修復的程式碼片段**：
  在刪除牌組後，清除所有不再屬於任何牌組的卡片。
  ```python
  def delete_deck(deck_id):
      conn = get_db_connection()
      try:
          with conn:
              conn.execute("DELETE FROM deck_folders WHERE deck_id = ?", (deck_id,))
              conn.execute("DELETE FROM card_decks WHERE deck_id = ?", (deck_id,))
              conn.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
              # 清除不再屬於任何牌組的卡片
              conn.execute("DELETE FROM cards WHERE id NOT IN (SELECT DISTINCT card_id FROM card_decks)")
      finally:
          conn.close()
  ```

---

### Bug 25: 預設寫死且不安全的 `SECRET_KEY` (Hardcoded Security Key)
* **檔案路徑與精確行號**：`config.py` 第 8 行
* **靜態分析原因解釋**：
  `config.py` 中的 `SECRET_KEY` 配置在環境變數不存在時會回退（fallback）到寫死的 `'default-dev-secret-key-change-me'`。在生產環境部署中，如果使用者沒有顯式配置環境變數，該寫死的金鑰會導致 Session 容易被偽造與篡改，存在嚴重的安全性隱患。
* **具體修復建議與建議修復的程式碼片段**：
  在生產環境下如果沒有配置環境變數應直接報錯中斷啟動，或者在啟動時動態生成隨機金鑰（但這會導致重啟後舊 Session 失效）：
  ```python
  # 修改 config.py：
  class Config:
      SECRET_KEY = os.environ.get('SECRET_KEY')
      if not SECRET_KEY:
          # 若非開發環境，強制拋出異常
          if os.environ.get('FLASK_ENV') == 'production':
              raise RuntimeError("生產環境下必須配置 SECRET_KEY 環境變數！")
          SECRET_KEY = 'default-dev-secret-key-change-me'
  ```

---

### Bug 26: 於生產/預設環境下以 `debug=True` 運行 Flask 應用程式 (Flask App Run in Debug Mode)
* **檔案路徑與精確行號**：`app.py` 第 442 行
* **靜態分析原因解釋**：
  在 `app.py` 的進入點中，代碼直接寫死了 `debug=True`：
  ```python
  app.run(host='0.0.0.0', port=10000, debug=True)
  ```
  在生產環境中運行 Debug 模式是一個巨大的安全性風險。Werkzeug 除錯器會在頁面出錯時將呼叫棧與互動式控制台暴露給前端，允許任何訪問網站的使用者在伺服器端執行任意 Python 代碼，導致伺服器主機面臨被接管（RCE）的威脅。
* **具體修復建議與建議修復的程式碼片段**：
  根據環境變數 `FLASK_DEBUG` 或 `FLASK_ENV` 動態決定是否開啟 debug 模式，預設設為 `False`：
  ```python
  if __name__ == '__main__':
      # 從環境變數獲取 debug 配置，預設為 False
      debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1')
      app.run(host='0.0.0.0', port=10000, debug=debug_mode)
  ```

---
*報告完畢。所有條目均已通過靜態邏輯審查，確保無誤。本報告未修改專案內部的任何原始碼。*
