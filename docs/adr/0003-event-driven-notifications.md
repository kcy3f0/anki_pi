# ADR-003: Event-Driven Notifications (Side Effect Extraction)

## Context
`send_discord_message` was called from 7 domain functions (`submit_card_review`, `reset_all_learning_progress`, `delete_all_app_data`, `import_csv_data`, `create_exam`, `delete_exam`, `import_exams_csv`). Side effects mixed into pure domain logic, making tests require monkey-patching or real network calls.

## Decision
Extract notifications to **event-driven model**:
1. Domain modules return **events** (dataclasses) instead of calling notifier.
2. `app.py` routes collect events and dispatch to `Notifier` implementation.
3. `Notifier` Protocol: `notify(event: NotificationEvent)`.
4. Two adapters: `DiscordNotifier` (async thread), `NullNotifier` (test).

## Consequences
- ✅ **Pure domain**: Repos/Schedulers have no side effects, easy to reason about and test.
- ✅ **Observability**: Adding Email/Slack/push only needs new `Notifier` adapter.
- ✅ **Test isolation**: Unit tests use `NullNotifier`, verify event payload without network.
- ⚠️ Callers must explicitly dispatch events (no automatic middleware). Acceptable for ~20 POST routes.
