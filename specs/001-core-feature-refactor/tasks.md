# Tasks: Core Feature Refactor

**Input**: Design documents from `specs/001-core-feature-refactor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Tests are MANDATORY for all refactored or added modules, as per Constitution Principle III. Ensure all tests pass before implementation is considered complete.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure (src/models, src/services, src/web, tests/unit, tests/integration)
- [X] T002 [P] Configure `src/config.py` using `python-dotenv` for environment variables
- [X] T003 [P] Initialize `src/app.py` with application factory pattern `create_app()`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/models/database.py` with `get_db_connection` and thread-safe connection pool
- [X] T005 [P] Implement `src/models/migrations.py` to handle legacy schema checks and migrations from `app.py`
- [X] T006 [P] Configure Flask-WTF and CSRF protection in `src/app.py`
- [X] T007 Create `src/utils/date_helpers.py` for ISO8601 string/datetime conversions used across layers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Spaced Repetition Review (Priority: P1) 🎯 MVP

**Goal**: Implement the core FSRS-based review logic in a modular fashion.

**Independent Test**: Verify that a card's FSRS state updates correctly after a simulated review session using a test database.

### Tests for User Story 1 (MANDATORY)

- [X] T008 [P] [US1] Unit test for FSRS scheduling in `tests/unit/services/test_study_service.py`
- [X] T009 [P] [US1] Integration test for review flow in `tests/integration/test_review_flow.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `src/models/card.py` with Card entity and state mapping
- [X] T011 [P] [US1] Implement `src/models/deck.py` for deck-card relationship queries
- [X] T012 [US1] Implement `src/services/study_service.py` with FSRS review logic and next card selection
- [X] T013 [US1] Create `src/web/routes/study.py` Blueprint for study endpoints
- [X] T014 [US1] Integrate `study` blueprint into `src/app.py` factory

**Checkpoint**: User Story 1 (MVP) is fully functional and testable independently.

---

## Phase 4: User Story 4 - Data Persistence & Continuity (Priority: P1)

**Goal**: Ensure existing `flashcards.db` is correctly handled and backed up.

**Independent Test**: Successfully load a legacy `flashcards.db` and verify all cards and folders are intact.

### Tests for User Story 4 (MANDATORY)

- [X] T015 [P] [US4] Integration test for legacy database compatibility in `tests/integration/test_db_compatibility.py`

### Implementation for User Story 4

- [X] T016 [US4] Refactor `backup_manager.py` into `src/utils/backup_manager.py` with automated backup triggers
- [X] T017 [US4] Implement schema validation in `src/models/migrations.py` to ensure `flashcards.db` readiness
- [X] T018 [US4] Refactor `restore.ps1` and `restore.sh` to point to the new project structure

**Checkpoint**: Data continuity is guaranteed; legacy databases are safely managed.

---

## Phase 5: User Story 2 - Card Import & Management (Priority: P1)

**Goal**: Implement modular card management and duplicate-merging CSV import.

**Independent Test**: Import a CSV with overlapping content and verify that cards are merged rather than duplicated.

### Tests for User Story 2 (MANDATORY)

- [X] T019 [P] [US2] Unit test for CSV merging logic in `tests/unit/services/test_import_service.py`
- [X] T020 [P] [US2] Integration test for card management (Add/Edit/Delete) in `tests/integration/test_card_mgmt.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/models/folder.py` for folder-deck management
- [X] T022 [US2] Implement `src/services/import_service.py` with CSV parsing and "Merge Duplicates" logic
- [X] T023 [US2] Create `src/web/routes/cards.py` and `src/web/routes/decks.py` Blueprints
- [X] T024 [US2] Create `src/web/forms/card_forms.py` using Flask-WTF for input validation
- [X] T025 [US2] Implement "Reset Progress" and "Delete All Cards" logic in `src/services/admin_service.py`

**Checkpoint**: Card management and batch import are fully modularized and tested.

---

## Phase 6: User Story 3 - Daily Discord Notifications (Priority: P2)

**Goal**: Decouple notification logic and ensure daily reminders work.

**Independent Test**: Manually trigger a notification and verify it arrives in Discord with correct due counts.

### Tests for User Story 3 (MANDATORY)

- [X] T026 [P] [US3] Unit test for notification message formatting in `tests/unit/services/test_notification_service.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `src/services/notification_service.py` for Discord Webhook integration
- [X] T028 [US3] Refactor `daily_reminder.py` into `src/utils/daily_reminder.py` to use `NotificationService`
- [X] T029 [US3] Refactor `discord_bot.py` into `src/services/discord_bot_service.py` if applicable

**Checkpoint**: Notification system is modular and decoupled from the web app.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, final validation, and decommissioning the monolith.

- [X] T030 [P] Update `README.md` and `GEMINI.md` to reflect the new modular project layout
- [X] T031 Perform final end-to-end manual validation of all features on Raspberry Pi environment
- [X] T032 [P] Run `pytest` on the entire suite and ensure 100% pass rate
- [X] T033 Decommission legacy `app.py` after verifying all functionality is migrated to `src/`
- [X] T034 Validate `quickstart.md` steps from a fresh environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 (Structure and Config).
- **User Stories (Phase 3+)**: All depend on Phase 2 completion (Database and Base App).
- **Polish (Final Phase)**: Depends on all User Stories being migrated and verified.

### Parallel Opportunities

- T002 and T003 can start together.
- T005, T006 can run in parallel within Phase 2.
- Once Phase 2 is complete, US1, US2, US3, and US4 can be developed in parallel if separate databases/mocks are used.
- All tasks marked [P] can run in parallel with other tasks in the same phase.

---

## Implementation Strategy

### MVP First (User Story 1 + Story 4)

1. Complete Setup and Foundation.
2. Complete US1 (Review) and US4 (Data Continuity) - this ensures the "Anki" part works and data is safe.
3. **STOP and VALIDATE**: Verify existing database loads and reviews update correctly.

### Incremental Delivery

1. Foundation ready.
2. Add Review logic (US1) -> Deliver.
3. Add Data Safety (US4) -> Deliver.
4. Add Management/Import (US2) -> Deliver.
5. Add Notifications (US3) -> Deliver.
6. Cleanup monolith.
