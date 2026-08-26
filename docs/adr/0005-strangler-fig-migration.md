# ADR-005: Strangler Fig Migration (Zero-Downtime Compatibility)

## Context
Full rewrite of `database.py` risky: 1320 lines, 7 integration tests, production `flashcards.db` must survive unchanged. Big-bang rewrite would break `app.py` routes and tests simultaneously.

## Decision
**Strangler Fig pattern**: New modules alongside old, gradual delegation.

### Phase 0: Foundation
Create `domain/` (protocols, models, events, time_provider), `adapters/` (sqlite, memory, schema).

### Phase 1: Adapter Online
`SqliteAdapter` implements `DatabaseAdapter`. `database.py` keeps all functions but internally calls `adapter.execute()` — **zero SQL changes, zero Schema changes, existing DB 100% compatible**.

### Phase 2: Extract FsrcScheduler
Move FSRS logic to `FsrcSchedulerImpl`. `database.submit_card_review` delegates to it + adapter for persistence.

### Phase 3: Extract ExamScheduler
Move exam distribution, due cards, expired processing to `ExamSchedulerImpl`.

### Phase 4: Extract Repos
`CardRepoImpl`, `FolderDeckRepoImpl`, `SettingsRepoImpl` take over CRUD.

### Phase 5: Cleanup
`database.py` becomes thin facade (current state). Optionally remove entirely, update `app.py` to use factory.

### Verification
Each phase: run full `test_exam_scheduling.py` (7 integration tests) — **must pass without modification**.

## Consequences
- ✅ **Zero risk**: Production DB never migrated, never touched.
- ✅ **Incremental**: Each phase verifiable, rollback = revert `database.py`.
- ✅ **Tests unchanged**: Existing integration tests continue working throughout.
- ✅ **Learning**: Team learns new architecture incrementally.
