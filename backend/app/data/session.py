from fastapi import Request
from sqlalchemy.orm import sessionmaker


def create_session_factory(engine):
    """Create the scoped SQLAlchemy session factory for FastAPI dependencies."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request):
    """Yield one database session for the lifetime of an HTTP request."""
    with request.app.state.session_factory() as session:
        yield session
