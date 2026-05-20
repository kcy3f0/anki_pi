# Data Model: Anki Pi (Legacy Schema Preservation)

This document describes the existing SQLite database schema that MUST be preserved or migrated non-destructively during the refactoring process.

## Tables

### `cards`
Stores the flashcard content and its FSRS learning state.
- `id` (INTEGER, PK): Unique identifier.
- `front` (TEXT): The English word or question.
- `back` (TEXT): The translation or answer.
- `next_review` (DATE/ISO8601): When the card is due for review.
- `state` (INTEGER): FSRS state (1=New, 2=Review, 3=Learning, 4=Relearning).
- `step` (INTEGER): FSRS learning step.
- `stability` (FLOAT): FSRS stability value.
- `difficulty` (FLOAT): FSRS difficulty value.
- `last_review` (DATE/ISO8601): When the card was last reviewed.
- `reps` (INTEGER): Total number of reviews.
- `lapses` (INTEGER): Number of times the user forgot the card.
- `card_type` (TEXT): 'recognize' or 'spell'.

### `decks`
Stores card collections.
- `id` (INTEGER, PK): Unique identifier.
- `name` (TEXT, UNIQUE): Name of the deck.

### `folders`
Stores containers for decks.
- `id` (INTEGER, PK): Unique identifier.
- `name` (TEXT, UNIQUE): Name of the folder.

### `card_decks` (Junction Table)
Maps cards to one or more decks (M:N).
- `card_id` (INTEGER, FK): Reference to `cards.id`.
- `deck_id` (INTEGER, FK): Reference to `decks.id`.
- *Constraints*: Composite PK (card_id, deck_id), ON DELETE CASCADE.

### `deck_folders` (Junction Table)
Maps decks to one or more folders (M:N).
- `deck_id` (INTEGER, FK): Reference to `decks.id`.
- `folder_id` (INTEGER, FK): Reference to `folders.id`.
- *Constraints*: Composite PK (deck_id, folder_id), ON DELETE CASCADE.

### `settings`
Stores global application configuration.
- `key` (TEXT, PK): Setting name.
- `value` (TEXT): Setting value.

## Migration Requirements
- Any change to these tables must be handled by `src/models/migrations.py`.
- New tables (if any) must follow the same naming and constraint conventions.
