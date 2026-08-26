# ADR-004: TimeProvider Abstraction

## Context
Time handling scattered across 10+ locations: `datetime.now()`, `get_day_cutoff_utc()` (hardcoded UTC+8), `parse_db_datetime()` (120 lines, timezone suffixes, microsecond truncation), `parse_input_datetime()`. Tests needed to mock `datetime.now()` for deterministic "exam countdown", "daily new card reset", "FSRS interval" verification.

## Decision
Introduce `TimeProvider` Protocol (4 methods):
- `now_utc() -> datetime`
- `day_cutoff_utc(tz_offset_hours=8, rollover_hour=4) -> datetime`
- `parse_iso(text) -> datetime` (full `parse_db_datetime` logic)
- `format_iso(dt) -> str`

Two adapters:
- `SystemTimeProvider`: real time.
- `FixedTimeProvider`: test-controlled (`set_now`, `advance`).

All modules inject `TimeProvider` instead of calling `datetime.now()`.

## Consequences
- ✅ **Locality**: Timezone policy changes (DST, multi-tz) only touch `SystemTimeProvider`.
- ✅ **Deterministic tests**: `FixedTimeProvider` enables exact time-travel for "exam in 5 days", "rollover at 04:00".
- ✅ **Small interface**: 4 methods replace 10+ scattered time calls.
