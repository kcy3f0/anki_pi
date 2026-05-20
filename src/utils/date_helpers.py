from datetime import datetime, timezone

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

def parse_iso(date_str):
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(str(date_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None

def format_iso(dt):
    if not dt:
        return None
    return dt.isoformat()
