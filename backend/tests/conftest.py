import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'requests.db').as_posix()}",
    )
    application = create_app(settings)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def request_payload():
    return {
        "requester_name": "Mohammed Buckas",
        "requester_email": "mohammed@example.com",
        "asset_type": "Laptop",
        "reason": "Replacement laptop required for development work.",
    }
