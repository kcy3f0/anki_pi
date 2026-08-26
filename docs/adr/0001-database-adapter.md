# ADR-001: DatabaseAdapter Protocol for Persistence Seam

## Context
`database.py` (1320 lines) coupled domain logic (FSRS, exam scheduling, card merging) directly to SQLite via `get_db_connection()` and raw SQL. Tests required real database file, ran slowly, could not run in parallel.

## Decision
Introduce `DatabaseAdapter` Protocol (4 methods: `execute`, `execute_many`, `transaction`, `last_row_id`) with two adapters:
- `SqliteAdapter`: wraps existing `sqlite3.connect()` logic, **zero SQL changes**, **zero Schema changes**, existing `flashcards.db` works unchanged.
- `InMemoryAdapter`: SQLite `:memory:` with same Schema for fast unit tests.

All domain modules (Repos, Schedulers) depend on `DatabaseAdapter`, not concrete SQLite.

## Consequences
- ✅ Tests run in-memory, milliseconds per test, parallel-safe.
- ✅ Future PostgreSQL/Turso only needs new adapter.
- ✅ Existing production database 100% compatible.
- ⚠️ SQL strings remain in Repo implementations (not in Protocol). Acceptable trade-off for migration speed.
