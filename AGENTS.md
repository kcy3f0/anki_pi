# Anki Pi - Agent Instructions

## Project Overview
Flask + FSRS spaced repetition web app for Raspberry Pi/Intranet. Key components:
- **Backend**: `app.py` (Flask routes), `database.py` (SQLite + FSRS logic), `forms.py` (WTForms), `config.py` (env config)
- **Frontend**: Templates in `templates/`, static assets in `static/`
- **Database**: `flashcards.db` (SQLite, auto-created)

## Quick Start (Development)
```bash
# Linux/Raspberry Pi
./install.sh    # Creates venv, .env, systemd service, starts on port 10000

# Windows
.\install.ps1   # Creates venv, .env, desktop shortcut
```

## Running the App
```bash
# Direct (dev)
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
python app.py              # Runs on 0.0.0.0:10000

# Production (Linux)
sudo systemctl start anki_pi
sudo systemctl status anki_pi
```

## Key Commands
| Task | Command |
|------|---------|
| Install deps | `./venv/bin/pip install -r requirements.txt` |
| Update app | `./update.sh` (backs up DB, git pulls, updates deps, restarts service) |
| Restore DB | `./restore.sh` (lists backups, restores selected) |
| Run tests | `python test_exam_scheduling.py` |
| Format/lint | *No configured tools* - use standard Python style |

## Testing
- **Test file**: `test_exam_scheduling.py` (integration tests for exam scheduling, FSRS, card merging)
- **Run**: `python test_exam_scheduling.py` (requires database; runs against actual `flashcards.db`)
- Tests create/cleanup their own data but need DB connection

## Architecture Notes
- **FSRS scheduling**: `database.py:555-672` (`submit_card_review`) uses `fsrs` package
- **Exam scheduling**: Cards auto-distributed before exams (`distribute_exam_cards` at line 754)
- **Day rollover**: 04:00 UTC+8 cutoff (`get_day_cutoff_utc` at line 65)
- **Duplicate merging**: Cards with same `front` merge backs (`add_card` at line 296, `import_csv_data` at 361)
- **Discord webhook**: Async thread in `send_discord_message` (line 79)

## Database Schema (Key Tables)
- `folders`, `decks`, `deck_folders` (many-to-many)
- `cards`, `card_decks` (many-to-many)
- `exams`, `exam_decks`, `exam_folders`
- `revlog` (review history)
- `settings` (key-value: `desired_retention`, `fsrs_weights`, `daily_new_limit`)

## Environment Variables (`.env`)
```
SECRET_KEY=...           # Auto-generated on install
DISCORD_WEBHOOK_URL=...  # Optional
DATABASE_PATH=flashcards.db  # Default
```

## Common Gotchas
1. **Don't run install/update as root** - scripts check `EUID != 0`
2. **DB is gitignored** - backups in `backups/` are the safety net
3. **Virtual env at `.venv/`** - activated in systemd via `Environment="PATH=.../venv/bin"`
4. **Port 10000** - hardcoded in `app.py:589` and systemd service
5. **CSRF protection** - all POST routes use `EmptyForm()` validation
6. **Timezone handling**: DB stores UTC; day cutoff at 04:00 local (UTC+8)

## File Structure
```
anki_pi/
├── app.py                 # Flask app, all routes
├── database.py            # All DB logic + FSRS + exam scheduling (1300+ lines)
├── config.py              # Config from .env
├── forms.py               # WTForms definitions
├── requirements.txt       # 5 deps: Flask, Flask-WTF, python-dotenv, fsrs, requests
├── install.sh / .ps1      # Setup scripts
├── update.sh / .ps1       # Update scripts (backup -> pull -> deps -> restart)
├── restore.sh / .ps1      # DB restore from backups/
├── test_exam_scheduling.py # Integration tests
├── templates/             # Jinja2 templates
├── static/                # CSS/JS
├── flashcards.db          # SQLite DB (gitignored)
├── backups/               # Auto-created on update
└── .venv/                 # Virtual env (gitignored)
```

## Important Patterns
- **DB connections**: Use `get_db_connection()` (line 10) - returns row_factory=sqlite3.Row
- **Transactions**: Use `with conn:` context manager for auto-commit/rollback
- **Datetime**: `format_datetime_for_db()` / `parse_db_datetime()` handle UTC ISO format
- **Flash messages**: All user feedback via `flash()` with categories: success/warning/danger/info
- **Redirects**: Use `is_safe_url()` for referrer redirects

## Agent skills

### Issue tracker

GitHub Issues via `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at repo root). See `docs/agents/domain.md`.