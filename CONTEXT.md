# Anki Pi - Domain Context

## Core Concepts

### Card
記憶卡，包含正面（front）、背面（back）、卡片類型（card_type: recognize/spell）、FSRS 排程狀態。

### Deck
牌組，卡片的容器。一張卡片可屬於多個牌組（多對多關聯 `card_decks`）。

### Folder
資料夾，群組牌組。一個牌組可屬於多個資料夾（多對多關聯 `deck_folders`）。

### Exam
考試行程，含名稱、日期、處理狀態。關聯牌組（`exam_decks`）與資料夾（`exam_folders`）。觸發卡片分發邏輯。

### Review
一次複習動作，含卡片 ID、評分（1=Again, 2=Hard, 3=Good, 4=Easy）、產生下次排程時間。

### Revlog
複習歷史記錄，供統計與匯出。

### CardScope
卡片查詢範圍類型：`deck_id` | `folder_id` | `exam_id`（三選一）。

### ExamScope
考試排程範圍類型：`deck_id` | `folder_id` | `exam_id`（三選一）。

### SchedulePlan
單張卡片的排程計畫：`card_id` + `next_review`。

### DueCards
當日到期卡片集合：`new_cards` (List[CardRow]) + `due_cards` (List[CardRow])。

### CardState
FSRS 排程所需的卡片狀態快照（id, state, step, stability, difficulty, last_review, due, reps, lapses）。

### ScheduledReview
排程結果：`next_review`, `state`, `step`, `stability`, `difficulty`, `last_review`。

---

## Modules (Deep Modules)

| Module | 負責領域 | 關鍵介面 |
|--------|----------|----------|
| **DatabaseAdapter** | 持久化縫合線 | `execute`, `execute_many`, `transaction`, `last_row_id` |
| **CardRepo** | 卡片 CRUD、匯入、合併 | `get_by_id`, `list`, `add`, `update`, `delete`, `import_csv`, `get_card_state`, `save_review`, `save_revlog` |
| **FolderDeckRepo** | 資料夾/牌組 CRUD、關聯 | `list_folders_with_decks`, `create_folder`, `delete_folder`, `create_deck`, `update_deck`, `delete_deck`, `get_deck_folders`, `list_all_decks`, `list_all_folders` |
| **SettingsRepo** | 設定鍵值存取 | `get`, `set` |
| **FsrcScheduler** | FSRS 排程核心（純演算法） | `review`, `get_parameters`, `set_parameters` |
| **ExamScheduler** | 考試卡片分發、到期查詢、過期處理 | `distribute`, `get_due_cards`, `process_expired`, `get_all_exams`, `create_exam`, `delete_exam` |
| **TimeProvider** | 時間存取抽象 | `now_utc`, `day_cutoff_utc`, `parse_iso`, `format_iso` |
| **Notifier** | 通知發送抽象 | `notify` |

---

## Events

- `CardReviewedEvent` - 複習完成
- `ProgressResetEvent` - 進度重置
- `DataClearedEvent` - 資料清空
- `CardsImportedEvent` - 卡片匯入
- `ExamCreatedEvent` - 考試建立
- `ExamDeletedEvent` - 考試刪除
- `ExamsImportedEvent` - 考試批次匯入

---

## Adapters

| Adapter | 環境 | 說明 |
|---------|------|------|
| **SqliteAdapter** | 生產 | 包裝現有 SQLite 連線與手寫 SQL，**零 Schema 變更**、**現有 `flashcards.db` 直接相容** |
| **InMemoryAdapter** | 測試 | SQLite `:memory:` 共用相同 Schema，毫秒級測試 |
| **DiscordNotifier** | 生產 | 非同步執行緒發送 Discord Webhook |
| **NullNotifier** | 測試/停用 | 記憶體內收集事件，不發送 |
| **SystemTimeProvider** | 生產 | 真實系統時間 |
| **FixedTimeProvider** | 測試 | 可控制時間流逝 (`set_now`, `advance`) |

---

## Architecture Decisions (ADR Index)

- [ADR-001: DatabaseAdapter Protocol](docs/adr/0001-database-adapter.md)
- [ADR-002: Module Decomposition](docs/adr/0002-module-decomposition.md)
- [ADR-003: Event-Driven Notifications](docs/adr/0003-event-driven-notifications.md)
- [ADR-004: TimeProvider Abstraction](docs/adr/0004-time-provider.md)
- [ADR-005: Strangler Fig Migration](docs/adr/0005-strangler-fig-migration.md)
