# ADR-002: Module Decomposition (Deep Modules)

## Context
`database.py` was a **shallow module** (Ousterhout): ~1320 lines, 50+ functions, 5 domains (CRUD, FSRS, Exam scheduling, Settings, Notifications) all mixed. Interface complexity ≈ implementation complexity. Deletion test confirmed: removing it would scatter complexity across all callers.

## Decision
Decompose into **5 deep modules** + adapters, each with small interface hiding large implementation:

| Module | Interface Size | Hidden Complexity |
|--------|----------------|-------------------|
| `CardRepo` | 9 methods | SQL, merge logic, CSV import |
| `FolderDeckRepo` | 9 methods | JOIN queries, stats aggregation |
| `SettingsRepo` | 2 methods | Key-value storage |
| `FsrcScheduler` | 3 methods | FSRS algorithm, exam capping, parameter management |
| `ExamScheduler` | 7 methods | 7-day cutoff, jitter distribution, expired exam chain reschedule, overlap recalculation |

Plus shared `DatabaseAdapter` seam.

## Consequences
- ✅ **Locality**: FSRS changes only touch `FsrcScheduler`; exam deadline logic only in `ExamScheduler`.
- ✅ **Leverage**: Callers (`app.py`, tests) depend on 5 small interfaces vs 50+ functions.
- ✅ **Testability**: Each module unit-testable via `InMemoryAdapter` + `FixedTimeProvider`.
- ✅ **Replaceability**: New scheduling algorithms (SM-2, custom) only need new `FsrcScheduler` adapter.
