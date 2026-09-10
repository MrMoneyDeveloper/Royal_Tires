import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.models.asset_request import AssetRequest


@pytest.fixture
def webhook_app(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'webhook.db').as_posix()}",
        app_username="test-user",
        app_password="unit-test-password",
        frontend_url="https://portal.example.com",
        zendesk_webhook_secret="webhook-secret",
    )
    application = create_app(settings)
    yield application
    application.state.engine.dispose()


def seed_request(app):
    with app.state.session_factory() as db:
        record = AssetRequest(
            requester_name="Farhaan Buckas",
            requester_email="farhaan@example.com",
            asset_type="Laptop",
            reason="Laptop required for technical implementation work.",
            status="new",
            zendesk_ticket_id=9001,
            zendesk_status="new",
            zendesk_sync_status="synced",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id


def event(status="open", external_id=None):
    body = {
        "event": "status_changed",
        "ticket_id": 9001,
        "status": status,
    }
    if external_id is not None:
        body["external_id"] = external_id
    return body


def test_webhook_requires_separate_bearer_secret(webhook_app):
    seed_request(webhook_app)
    with TestClient(webhook_app) as client:
        response = client.post("/api/webhooks/zendesk", json=event())
        assert response.status_code == 401
        response = client.post(
            "/api/webhooks/zendesk",
            json=event(),
            headers={"Authorization": "Bearer wrong"},
        )
        assert response.status_code == 401


def test_webhook_updates_status_visible_to_tracking_api(webhook_app):
    request_id = seed_request(webhook_app)
    with TestClient(webhook_app) as client:
        response = client.post(
            "/api/webhooks/zendesk",
            json=event("pending", f"royal-tires-asset-{request_id}"),
            headers={"Authorization": "Bearer webhook-secret"},
        )
        assert response.status_code == 200
        assert response.json()["changed"] is True

        client.auth = ("test-user", "unit-test-password")
        tracked = client.get(f"/api/requests/{request_id}")
        assert tracked.status_code == 200
        assert tracked.json()["status"] == "pending"
        assert tracked.json()["zendesk_status"] == "pending"
        assert tracked.json()["zendesk_sync_status"] == "synced"
        assert tracked.json()["zendesk_last_synced_at"] is not None


def test_duplicate_webhook_is_idempotent(webhook_app):
    request_id = seed_request(webhook_app)
    headers = {"Authorization": "Bearer webhook-secret"}
    body = event("open", f"royal-tires-asset-{request_id}")
    with TestClient(webhook_app) as client:
        first = client.post("/api/webhooks/zendesk", json=body, headers=headers)
        second = client.post("/api/webhooks/zendesk", json=body, headers=headers)
    assert first.status_code == 200
    assert first.json()["changed"] is True
    assert second.status_code == 200
    assert second.json()["changed"] is False


def test_webhook_rejects_mismatched_external_id(webhook_app):
    seed_request(webhook_app)
    with TestClient(webhook_app) as client:
        response = client.post(
            "/api/webhooks/zendesk",
            json=event("open", "royal-tires-asset-999"),
            headers={"Authorization": "Bearer webhook-secret"},
        )
    assert response.status_code == 409
