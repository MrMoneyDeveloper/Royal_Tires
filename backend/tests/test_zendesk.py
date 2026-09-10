import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.models.audit_log import AuditLog
from app.models.zendesk_connection import ZendeskConnection
from app.services import zendesk_service


@pytest.fixture
def zendesk_app(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'zendesk.db').as_posix()}",
        app_username="test-user",
        app_password="unit-test-password",
        frontend_url="https://portal.example.com",
        config_encryption_key="unit-test-encryption-key-that-is-long-enough",
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


def seed_configured_connection(app):
    with app.state.session_factory() as db:
        connection = ZendeskConnection(
            id=1,
            subdomain="example",
            api_email="admin@example.com",
            encrypted_api_token=zendesk_service._encrypt_token(
                app.state.settings, "unit-test-token"
            ),
            connected_user_name="Admin User",
            connected_user_email="admin@example.com",
            connected_user_role="admin",
            brand_id=101,
            group_id=102,
            ticket_form_id=103,
            asset_type_field_id=104,
            local_request_id_field_id=105,
            request_source_field_id=106,
            view_id=107,
        )
        db.add(connection)
        db.commit()


def test_connect_validates_login_and_returns_dry_run_plan(
    monkeypatch, zendesk_app, zendesk_client
):
    def fake_request(credentials, method, path, payload=None):
        assert credentials.token == "secret-token"
        assert method == "GET"
        assert path == "/api/v2/users/me.json"
        return {
            "user": {
                "id": 42,
                "name": "Zendesk Admin",
                "email": "admin@example.com",
                "role": "admin",
            }
        }

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    monkeypatch.setattr(
        zendesk_service,
        "build_setup_plan",
        lambda credentials: [
            {
                "key": "brand",
                "object_type": "Brand",
                "name": "Royal Tyres",
                "action": "create",
                "existing_id": None,
            }
        ],
    )

    response = zendesk_client.post(
        "/api/zendesk/connect",
        json={
            "subdomain": "example.zendesk.com",
            "email": "admin@example.com",
            "api_token": "secret-token",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["configured"] is False
    assert body["can_configure"] is True
    assert body["instance"] == "example.zendesk.com"
    assert body["plan"][0]["action"] == "create"
    assert len(body["plan_fingerprint"]) == 64

    with zendesk_app.state.session_factory() as db:
        stored = db.get(ZendeskConnection, 1)
        assert stored is not None
        assert stored.encrypted_api_token != "secret-token"
        assert zendesk_service._decrypt_token(
            zendesk_app.state.settings, stored.encrypted_api_token
        ) == "secret-token"


def test_apply_requires_explicit_confirmation(zendesk_client):
    response = zendesk_client.post(
        "/api/zendesk/apply",
        json={"confirm": False, "plan_fingerprint": "0" * 64},
    )
    assert response.status_code == 400


def test_apply_rejects_stale_reviewed_plan(monkeypatch, zendesk_app, zendesk_client):
    seed_configured_connection(zendesk_app)
    monkeypatch.setattr(zendesk_service, "build_setup_plan", lambda credentials: [])

    response = zendesk_client.post(
        "/api/zendesk/apply",
        json={"confirm": True, "plan_fingerprint": "0" * 64},
    )

    assert response.status_code == 409
    assert "Refresh the dry-run plan" in response.json()["detail"]


def test_apply_stores_discovered_configuration_ids(
    monkeypatch, zendesk_app, zendesk_client
):
    seed_configured_connection(zendesk_app)
    with zendesk_app.state.session_factory() as db:
        connection = db.get(ZendeskConnection, 1)
        for field in zendesk_service.ID_FIELDS:
            setattr(connection, field, None)
        db.commit()

    monkeypatch.setattr(zendesk_service, "_ensure_brand", lambda credentials: 201)
    monkeypatch.setattr(zendesk_service, "_ensure_group", lambda credentials: 202)
    field_ids = iter([203, 204, 205])
    monkeypatch.setattr(
        zendesk_service, "_ensure_field", lambda credentials, definition: next(field_ids)
    )
    monkeypatch.setattr(
        zendesk_service,
        "_ensure_form",
        lambda credentials, brand_id, field_ids: 206,
    )
    monkeypatch.setattr(
        zendesk_service, "_ensure_view", lambda credentials, group_id: 207
    )
    monkeypatch.setattr(
        zendesk_service,
        "_verify_object",
        lambda credentials, object_type, object_id, path, root_key: {
            "object_type": object_type,
            "id": object_id,
            "ok": True,
            "result": "PASS",
        },
    )
    monkeypatch.setattr(zendesk_service, "build_setup_plan", lambda credentials: [])

    preview = zendesk_client.get("/api/zendesk/setup")
    assert preview.status_code == 200
    fingerprint = preview.json()["plan_fingerprint"]

    response = zendesk_client.post(
        "/api/zendesk/apply",
        json={"confirm": True, "plan_fingerprint": fingerprint},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is True
    assert body["ids"]["brand_id"] == 201
    assert body["ids"]["view_id"] == 207
    assert len(body["verification"]) == 7
    assert all(item["ok"] for item in body["verification"])


def test_successful_zendesk_create_updates_local_request(
    monkeypatch, zendesk_app, zendesk_client
):
    seed_configured_connection(zendesk_app)
    monkeypatch.setattr(
        zendesk_service,
        "create_ticket",
        lambda settings, db, record: {"id": 98765, "status": "new"},
    )

    response = zendesk_client.post("/api/requests", json=payload())

    assert response.status_code == 201
    body = response.json()
    assert body["zendesk_ticket_id"] == 98765
    assert body["zendesk_status"] == "new"
    assert body["zendesk_sync_status"] == "synced"
    assert body["zendesk_last_synced_at"] is not None
    assert audit_events(zendesk_app) == ["REQUEST_CREATED", "ZENDESK_TICKET_CREATED"]


def test_zendesk_failure_keeps_primary_request(
    monkeypatch, zendesk_app, zendesk_client
):
    seed_configured_connection(zendesk_app)

    def fail_create(settings, db, record):
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
