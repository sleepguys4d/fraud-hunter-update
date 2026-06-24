from datetime import datetime, timezone


def now_utc() -> datetime:
    """UTC naive — consistente com o armazenamento SQLite/Postgres sem tz."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
