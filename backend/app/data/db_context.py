from sqlalchemy import create_engine, event


def create_db_engine(database_url: str):
    """Create the SQLAlchemy engine used by the application composition root."""
    if database_url.startswith(("postgres://", "postgresql://")):
        database_url = "postgresql+psycopg://" + database_url.split("://", 1)[1]

    sqlite = database_url.startswith("sqlite:")
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
