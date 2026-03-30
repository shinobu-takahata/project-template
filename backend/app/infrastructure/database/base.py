from datetime import UTC, datetime

from app.core.database import Base


def utc_now():
    """UTC現在時刻を返す"""
    return datetime.now(UTC)


__all__ = ["Base", "utc_now"]
