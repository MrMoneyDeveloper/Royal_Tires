import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.audit_log import AuditLog
from app.services import zendesk_service


@pytest.fixture
def zendesk_app(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'zendesk.db').as_posix()}",
        app_username="test-user",
        app_password="unit-test-password",
        frontend_url="https://portal.example.com",
        zendesk_subdomain="example",
        zendesk_email="agent@example.com",
        zendesk_api_token="unit-test-token",
    )
    application = create_app(settings)
    yield application
    application.state.engine.dispose()


@pytest.fixture
def zendesk_client(zendesk_app):
    with TestClient(zendesk_app) as test_client:
        test_client.auth = ("test-user", "unit-test-password")
        yield test_client


def payload():
    return {
        "requester_name": "Farhaan Buckas",
        "requester_email": "farhaan@example.com",
        "asset_type": "Laptop",
        "reason": "Laptop required for technical implementation work.",
    }


def audit_events(app):
    with app.state.session_factory() as db:
        return list(db.scalars(select(AuditLog.event_type).order_by(AuditLog.id)))


def test_successful_zendesk_create_updates_local_request(monkeypatch, zendesk_app, zendesk_client):
    monkeypatch.setattr(
        zendesk_service,
        "create_ticket",
        lambda settings, record: {"id": 98765, "status": "new"},
    )

    response = zendesk_client.post("/api/requests", json=payload())

    assert response.status_code == 201
    body = response.json()
    assert body["zendesk_ticket_id"] == 98765
    assert body["zendesk_status"] == "new"
    assert body["zendesk_sync_status"] == "synced"
    assert body["zendesk_last_synced_at"] is not None
    assert audit_events(zendesk_app) == ["REQUEST_CREATED", "ZENDESK_TICKET_CREATED"]


def test_zendesk_failure_keeps_primary_request(monkeypatch, zendesk_app, zendesk_client):
    def fail_create(settings, record):
        raise zendesk_service.ZendeskError("simulated outage")

    monkeypatch.setattr(zendesk_service, "create_ticket", fail_create)

    response = zendesk_client.post("/api/requests", json=payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["zendesk_ticket_id"] is None
    assert body["zendesk_sync_status"] == "sync_failed"

    stored = zendesk_client.get(f"/api/requests/{body['id']}")
    assert stored.status_code == 200
    assert stored.json()["requester_name"] == "Farhaan Buckas"
    assert stored.json()["zendesk_sync_status"] == "sync_failed"
    assert audit_events(zendesk_app) == ["REQUEST_CREATED", "ZENDESK_CREATE_FAILED"]
