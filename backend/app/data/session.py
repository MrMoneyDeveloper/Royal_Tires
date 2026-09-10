"""
ROLE: Data infrastructure: session factory and scoped dependency
CALLED BY: main.create_app and Controllers through Depends(get_db)
CALLS: SQLAlchemy sessionmaker bound to the shared Engine
DATA IN: Engine or FastAPI Request carrying app state
DATA OUT: One Session yielded per HTTP request, closed afterward
WHY: Give repositories/services one shared unit of work per request.
SECURITY / RELIABILITY: Services explicitly commit; closing the Session releases connections
    and rolls back uncommitted work. Repositories receive/use this Session rather than
    independently creating network connections.
FLOW: main.create_app and Controllers through Depends(get_db) -> this module -> SQLAlchemy
    sessionmaker bound to the shared Engine
"""

from fastapi import Request
from sqlalchemy.orm import sessionmaker


def create_session_factory(engine):
    """Create the scoped SQLAlchemy session factory for FastAPI dependencies."""
    # main.py stores this factory; each get_db call creates a Session sharing the configured Engine.
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request):
    """Yield one database session for the lifetime of an HTTP request."""
    # Yield one Session through Controller -> Service -> Repository; context exit releases it and rolls back uncommitted work.
    with request.app.state.session_factory() as session:
        yield session
