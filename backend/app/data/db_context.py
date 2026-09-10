"""
ROLE: Data infrastructure: SQLAlchemy engine construction
CALLED BY: main.create_app
CALLS: SQLAlchemy create_engine and SQLite connection event
DATA IN: DATABASE_URL supplied through Settings
DATA OUT: Engine with driver configuration and connection pool
WHY: Keep driver/connection policy in one place.
SECURITY / RELIABILITY: Normalizes PostgreSQL URLs to psycopg and enables local SQLite foreign
    keys. pool_pre_ping checks reused connections. Data package approximates
    ApplicationDbContext infrastructure; no literal Entity Framework DbContext exists.
FLOW: main.create_app -> this module -> SQLAlchemy create_engine and SQLite connection event
"""

from sqlalchemy import create_engine, event


def create_db_engine(database_url: str):
    """Create the SQLAlchemy engine used by the application composition root."""
    if database_url.startswith(("postgres://", "postgresql://")):
        database_url = "postgresql+psycopg://" + database_url.split("://", 1)[1]

    sqlite = database_url.startswith("sqlite:")
    # SQLAlchemy owns the driver/pool; data/session.py binds Sessions to this Engine rather than opening per-repository connections.
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if sqlite else {},
        pool_pre_ping=True,
    )

    if sqlite:

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine
