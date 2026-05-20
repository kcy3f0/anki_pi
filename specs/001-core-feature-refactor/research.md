# Research: Modularization Strategy for Anki Pi

## Current State Analysis

The current `app.py` is a 1153-line monolith performing the following functions:
- Database initialization and complex schema migrations (100-300 lines).
- FSRS algorithm integration and data mapping.
- Core business logic (fetch next card, calculate stats, import/merge cards).
- Web routing and request handling (Flask).
- Utility functions (backup integration, date helpers).

### Challenges
- **High Coupling**: Database logic is mixed with HTTP request handling.
- **Difficulty in Testing**: Testing business logic requires a full Flask application context and database setup.
- **Complexity**: `init_db()` handles many versions of migrations, making it hard to reason about.

## Target Architecture: Layered Modular Design

We will adopt a layered architecture within a `src/` directory:

1.  **Model Layer (`src/models/`)**:
    - Decouple raw SQLite queries into focused model classes or repository modules.
    - Entities: `Card`, `Deck`, `Folder`, `Settings`.
    - Handles schema consistency and basic CRUD.

2.  **Service Layer (`src/services/`)**:
    - Contains pure business logic.
    - `StudyService`: Handles FSRS scheduling, answer processing, and next card selection.
    - `ImportService`: Handles CSV parsing, duplicate merging, and batch updates.
    - `OrganizationService`: Handles folder/deck relationships.
    - `NotificationService`: Manages daily Discord reminders.

3.  **Web Layer (`src/web/`)**:
    - Flask Blueprints for clean routing.
    - `routes/`: UI and API endpoints.
    - `forms/`: WTForms definitions for validation.
    - Minimal logic: parse request → call service → render response.

4.  **Application Core (`src/app.py`)**:
    - Application factory pattern (`create_app()`).
    - Extension initialization (CSRF, context helpers).

## Database Compatibility Strategy

To ensure `flashcards.db` remains reusable:
- The existing schema MUST be preserved.
- We will move the complex `init_db()` logic into a dedicated migration manager (`src/models/migrations.py`).
- Every model will verify the schema on startup without destroying data.
- We will continue using raw SQL (or a lightweight wrapper) to avoid the overhead/complexity of a full ORM like SQLAlchemy for this resource-constrained project.

## Refactoring Plan (Incremental)

1.  **Step 1: Foundational**: Setup `src/` structure, config management, and database connection pool.
2.  **Step 2: Model Layer**: Migrate `init_db()` and basic card/deck/folder queries to `src/models/`.
3.  **Step 3: Service Layer**: Extract FSRS and Import logic into `src/services/`. Add unit tests.
4.  **Step 4: Web Layer**: Convert `app.py` routes into Flask Blueprints in `src/web/`.
5.  **Step 5: Integration**: Connect everything in the app factory and verify with integration tests.
6.  **Step 6: Cleanup**: Remove legacy code and deprecated functions.

## Unknowns & Decisions

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| Use ORM? | No | Stick to raw SQL/Lightweight models to keep the app "lightweight" and "Raspberry Pi friendly". |
| Folder Structure | `src/` root | Standard Python project layout that separates source from tests and config. |
| Configuration | `python-dotenv` | Standard, secure way to handle secrets like `DISCORD_WEBHOOK`. |
