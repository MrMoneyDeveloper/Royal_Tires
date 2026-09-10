"""
ROLE: Data foundation: declarative Base and UTC timestamp type
CALLED BY: SQLAlchemy Models; services use utc_now
CALLS: SQLAlchemy declarative mapping and datetime
DATA IN: Model definitions and database timestamp results
DATA OUT: Shared metadata registry and UTC-aware values
WHY: Share mapping infrastructure across models.
SECURITY / RELIABILITY: UTCDateTime restores UTC metadata when SQLite returns naive values.
    Base collects tables; it neither authenticates users nor owns business workflow.
FLOW: SQLAlchemy Models; services use utc_now -> this module -> SQLAlchemy declarative mapping
    and datetime
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


# Models inherit this registry; main.py uses its metadata to create missing tables at startup.
class Base(DeclarativeBase):
    """Declarative base shared by all persisted models."""

    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Keep API timestamps UTC even when local SQLite drops timezone metadata."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            # Restore SQLite's missing timezone before ORM values reach response schemas and frontend date helpers.
            return value.replace(tzinfo=timezone.utc)
        return value
