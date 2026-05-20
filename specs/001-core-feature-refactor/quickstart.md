# Quickstart: Anki Pi Refactored Architecture

Welcome to the new modular Anki Pi. This architecture separates concerns into Web, Service, and Model layers.

## Project Layout

- `src/app.py`: Application entry point.
- `src/models/`: Data access logic (raw SQLite).
- `src/services/`: Business logic (FSRS, Import).
- `src/web/`: Flask Blueprints and routes.
- `tests/`: Automated test suite.

## Setup

1.  **Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your `SECRET_KEY` and `DISCORD_WEBHOOK_URL`.

3.  **Database**:
    Ensure `flashcards.db` is in the project root. The app will automatically run migrations on startup.

4.  **Run**:
    ```bash
    python src/app.py
    ```

## Testing

Run tests with pytest:
```bash
pytest tests/
```

- `pytest tests/unit`: Test individual services/models.
- `pytest tests/integration`: Test end-to-end flows using a temporary database.
