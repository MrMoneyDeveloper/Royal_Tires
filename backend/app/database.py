"""Compatibility facade for older imports.

New code should import from app.data. The implementation now lives in the
MVC data layer described in PROJECT_SPEC.md.
"""

from app.data import Base, UTCDateTime, create_db_engine, get_db, utc_now

__all__ = ["Base", "UTCDateTime", "create_db_engine", "get_db", "utc_now"]
