# Implementation Plan: Core Feature Refactor

**Branch**: `001-core-feature-refactor` | **Date**: 2026-05-19 | **Spec**: [specs/001-core-feature-refactor/spec.md]

**Input**: Feature specification from `specs/001-core-feature-refactor/spec.md`

## Summary
Refactor the monolithic `app.py` into a modular, layered architecture (Web, Service, Model) to improve maintainability and testability while ensuring 100% functional integrity and database backward compatibility.

## Technical Context

**Language/Version**: Python 3.x

**Primary Dependencies**: Flask, FSRS, Flask-WTF, python-dotenv

**Storage**: SQLite (`flashcards.db`)

**Testing**: pytest

**Target Platform**: Raspberry Pi / Local network (Windows/Linux support)

**Project Type**: Web application

**Performance Goals**: CSV import (100 cards) < 2s, Discord notifications delivered within 1m of 09:00.

**Constraints**: Responsive UI (Desktop/Mobile), No complex frontend frameworks (Vanilla JS), Mandatory backward compatibility with existing SQLite DB.

**Scale/Scope**: Personal/Intranet learning tool; must handle hundreds/thousands of cards efficiently.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Functional Integrity**: Existing tests pass (Regression Check)
- [x] **SOLID/DRY**: Architecture adheres to SOLID/DRY principles
- [x] **Testing Discipline**: Complete unit tests planned for new/refactored code
- [x] **Lightweight Architecture**: No unauthorized third-party dependencies
- [x] **Incremental**: Refactoring plan is broken into manageable steps
- [x] **Data Continuity**: Existing `flashcards.db` is reusable or a non-destructive migration script is provided

## Project Structure

### Documentation (this feature)

```text
specs/001-core-feature-refactor/
├── plan.md              # This file
├── research.md          # Modularization strategy
├── data-model.md        # Database schema preservation/migration
├── quickstart.md        # Developer setup for the new architecture
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/
├── app.py               # Application factory
├── config.py            # Configuration management
├── models/              # Data access layer (SQLite)
│   ├── card.py
│   ├── deck.py
│   └── folder.py
├── services/            # Business logic (FSRS, Import, Notifications)
│   ├── study_service.py
│   ├── import_service.py
│   └── notification_service.py
├── web/                 # Web layer (Blueprints)
│   ├── routes/
│   └── forms/
└── utils/               # Shared utilities (Backups, Date helpers)

tests/
├── unit/                # Individual module tests
├── integration/         # Service-level tests
└── e2e/                 # Web-level tests
```

**Structure Decision**: Adopted a layered architecture with `src/` as the root. This separates concerns (Web vs. Logic vs. Data) and facilitates unit testing each layer independently.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None      | N/A        | N/A                                 |
