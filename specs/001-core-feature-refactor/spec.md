# Feature Specification: Core Feature Preservation

**Feature Branch**: `001-core-feature-refactor`

**Created**: 2026-05-19

**Status**: Draft

**Input**: User description: "請讀取專案根目錄下的 readme.md。這份文件完整描述了專案目前的既有功能。請以此為唯一的範疇依據，為我生成一份詳細的功能規格書（Spec），列出所有重構時必須完整保留的核心邏輯、邊界條件（Edge Cases）與使用者情境。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Spaced Repetition Review (Priority: P1)

As a learner, I want to review my cards using the FSRS algorithm so that I can efficiently memorize content based on my performance.

**Why this priority**: Core value proposition of the application.

**Independent Test**: Can be tested by starting a review session, rating a card, and verifying the `next_review` date updates correctly in the database.

**Acceptance Scenarios**:

1. **Given** I have a card due for review, **When** I rate it as "Good", **Then** the card's stability and difficulty are updated via FSRS, and the next review date is set to a future date.
2. **Given** I am in a review session, **When** I click the audio icon, **Then** the pronunciation for the card's front side is played.
3. **Given** I am viewing a card, **When** I click the dictionary icon, **Then** I am redirected to the Cambridge dictionary for that word.

---

### User Story 2 - Card Import & Management (Priority: P1)

As a user, I want to import cards via CSV paste and manage them (add/edit/delete) to keep my learning material up to date.

**Why this priority**: Essential for populating the system with data.

**Independent Test**: Can be tested by pasting CSV content into the import tool and verifying the cards appear in the specified deck.

**Acceptance Scenarios**:

1. **Given** I have an existing card with content "apple,蘋果", **When** I import "apple,red fruit", **Then** the content is merged to "apple,蘋果 red fruit" (Merge Duplicates logic).
2. **Given** I choose the "Spell" card type, **When** I am tested with the back side (Chinese), **Then** I must type the exact front side (English) to pass.
3. **Given** I want to start fresh, **When** I trigger "Reset All Progress", **Then** all learning history is cleared but my cards remain.

---

### User Story 3 - Daily Discord Notifications (Priority: P2)

As a busy learner, I want to receive a daily Discord notification at 09:00 so that I don't forget to do my reviews.

**Why this priority**: High value for user retention and habit building.

**Independent Test**: Can be tested by triggering the notification script and verifying the message arrives in the configured Discord channel.

**Acceptance Scenarios**:

1. **Given** I have 5 cards due today, **When** it is 09:00, **Then** a Discord message is sent showing the total count (5) and a breakdown by deck.

---

### User Story 4 - Data Persistence & Continuity (Priority: P1)

As an existing user, I want the system to reuse my current `flashcards.db` or migrate it automatically so that I don't lose my cards and progress.

**Why this priority**: Preventing data loss is critical for user trust and continuity.

**Independent Test**: Can be tested by placing a legacy `flashcards.db` in the data directory and verifying the refactored app loads all cards and progress correctly.

**Acceptance Scenarios**:

1. **Given** an existing `flashcards.db` with legacy schema, **When** the new app starts, **Then** it either loads the data directly or performs a silent, non-destructive migration.
2. **Given** a need to revert, **When** I use the restore tool, **Then** I can select a previous backup from the `backups/` directory and restore it successfully.

---

### Edge Cases

- **Duplicate Imports**: Handled via concatenation instead of overwriting or creating separate entries.
- **Empty Decks/Folders**: The UI must handle navigation to empty containers without crashing.
- **Missing Audio**: If the TTS service/file is unavailable, the UI should fail gracefully without blocking the review flow.
- **FSRS Initialization**: New cards must be correctly initialized with default parameters (D, S) before the first review.
- **Database Schema Mismatch**: The system must detect and handle (via migration or error message) cases where the DB structure is incompatible with the current code.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use the FSRS algorithm library for all scheduling logic.
- **FR-002**: System MUST support "Recognize" and "Spell" card types with their respective study behaviors.
- **FR-003**: System MUST provide a CSV paste import feature that supports "apple,蘋果" format.
- **FR-004**: System MUST concatenate new content to existing content when a duplicate front-side is imported.
- **FR-005**: System MUST support organizing decks into multiple folders (M:N relationship).
- **FR-006**: System MUST send Discord notifications daily at 09:00 via Webhook.
- **FR-007**: System MUST provide a "Reset Progress" feature and a "Delete All Cards" feature.
- **FR-008**: System MUST perform automatic database backups to the `backups/` directory during updates.
- **FR-009**: System MUST be fully backward compatible with the existing `flashcards.db` schema or provide an automated migration script.
- **FR-010**: System MUST provide an external dictionary lookup link (default: Cambridge Dictionary).
- **FR-011**: System UI MUST be responsive and modern, supporting both desktop and mobile browsers.

### Key Entities

- **Card**: Represents the basic unit of learning. Attributes: Front, Back, Type, FSRS state (Stability, Difficulty, Elapsed Days, Scheduled Days, Last Review, Next Review).
- **Deck**: A collection of cards.
- **Folder**: A container for decks.
- **ReviewLog**: History of ratings for each card.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing cards and their learning history are preserved after refactoring/migration.
- **SC-002**: Users can complete a review session (10+ cards) with zero runtime errors.
- **SC-003**: CSV import of 100 cards takes less than 2 seconds.
- **SC-004**: Discord notifications are delivered within 1 minute of the scheduled time (09:00).
- **SC-005**: 100% of existing automated tests pass on the refactored codebase.
- **SC-006**: The application UI achieves a "mobile-friendly" score in standard browser testing tools.

## Assumptions

- **Environment**: Target environment remains Raspberry Pi / Local network.
- **Stack**: Python/Flask/SQLite remains the core technology choice.
- **Offline**: The system is primarily intended for local/intranet use, though Discord and Cambridge dictionary require internet access.
- **Data Location**: The `flashcards.db` file is expected to be in the project root or a configured data directory.
