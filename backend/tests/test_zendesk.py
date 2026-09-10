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
        zendesk_subdomain="example",
        zendesk_email="admin@example.com",
        zendesk_api_token="secret-token",
        zendesk_webhook_secret="webhook-unit-test-secret",
        zendesk_notification_email="farhaanhotd1@gmail.com",
        render_external_url="https://api.example.com",
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


def test_dropdown_definitions_use_zendesk_tagger_api_type():
    assert zendesk_service.FIELD_DEFINITIONS["asset_type_field"]["type"] == "tagger"
    assert zendesk_service.FIELD_DEFINITIONS["request_source_field"]["type"] == "tagger"


def test_asset_field_does_not_reuse_an_unrelated_option_tag(monkeypatch):
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", "secret-token")
    definition = zendesk_service.FIELD_DEFINITIONS["asset_type_field"]
    existing = [{"id": 50, "title": "Query Types", "type": "tagger",
                 "custom_field_options": [{"name": "Other", "value": "other"}]}]
    monkeypatch.setattr(zendesk_service, "_list_all", lambda *args: existing)
    calls = []

    def create_field(credentials, method, path, payload=None):
        calls.append((method, path))
        options = payload["ticket_field"]["custom_field_options"]
        assert {option["value"] for option in options}.isdisjoint({"other"})
        assert next(option["value"] for option in options if option["name"] == "Other") == "rt_asset_other"
        return {"ticket_field": {"id": 100}}

    monkeypatch.setattr(zendesk_service, "_request_json", create_field)
    assert zendesk_service._ensure_field(credentials, definition) == 100
    assert calls == [("POST", "/api/v2/ticket_fields.json")]
    assert existing[0]["custom_field_options"][0]["value"] == "other"


def test_existing_managed_asset_field_is_reused_without_mutation(monkeypatch):
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", "secret-token")
    definition = zendesk_service.FIELD_DEFINITIONS["asset_type_field"]
    monkeypatch.setattr(zendesk_service, "_list_all", lambda *args: [{"id": 100, **definition}])
    monkeypatch.setattr(zendesk_service, "_request_json", lambda *args: pytest.fail("REUSE must not write"))
    assert zendesk_service._ensure_field(credentials, definition) == 100


@pytest.mark.parametrize("asset", ["Laptop", "Monitor", "Mouse", "Keyboard", "Headset", "Docking Station", "Other"])
def test_ticket_asset_value_matches_provisioned_field(monkeypatch, zendesk_app, zendesk_client, asset):
    from app.models.asset_request import AssetRequest

    seed_configured_connection(zendesk_app)
    record = AssetRequest(id=27, **{**payload(), "asset_type": asset})
    captured = {}

    def create_ticket(credentials, method, path, body=None):
        captured.update(body["ticket"])
        return {"ticket": {"id": 98765, "status": "new"}}

    monkeypatch.setattr(zendesk_service, "_request_json", create_ticket)
    with zendesk_app.state.session_factory() as db:
        zendesk_service.create_ticket(zendesk_app.state.settings, db, record)
    selected = next(field["value"] for field in captured["custom_fields"] if field["id"] == 104)
    option = next(option for option in zendesk_service.FIELD_DEFINITIONS["asset_type_field"]["custom_field_options"] if option["name"] == asset)
    assert selected == option["value"]
    assert selected.startswith("rt_asset_")
    assert captured["external_id"] == "royal-tires-asset-27"
    assert "local_request_27" in captured["tags"]


def test_view_uses_valid_zendesk_subject_column_value(monkeypatch):
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", "secret-token")
    captured = {}
    monkeypatch.setattr(zendesk_service, "_list_all", lambda *args, **kwargs: [])

    def fake_request(credentials, method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)
        return {"view": {"id": 700}}

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    assert zendesk_service._ensure_view(credentials, 200) == 700
    columns = captured["payload"]["view"]["output"]["columns"]
    assert "description" in columns
    assert "subject" not in columns


def test_workflow_plan_includes_email_webhook_and_triggers(monkeypatch, zendesk_app):
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", "secret-token")
    monkeypatch.setattr(
        zendesk_service,
        "_discover",
        lambda credentials: {
            "brands": [], "groups": [], "fields": [], "forms": [], "views": [],
            "targets": [], "webhooks": [], "triggers": [],
        },
    )
    plan = zendesk_service.build_setup_plan(credentials, zendesk_app.state.settings)
    keys = {item["key"] for item in plan}
    assert {
        "email_target", "status_webhook", "trigger_new_email",
        "trigger_status_email", "trigger_status_sync",
    }.issubset(keys)
    target = next(item for item in plan if item["key"] == "email_target")
    assert "farhaanhotd1@gmail.com" in target["details"]


def test_trigger_templates_use_create_change_and_notification_actions():
    new_trigger = zendesk_service._new_request_email_trigger(123)
    status_email = zendesk_service._status_email_trigger(123)
    status_sync = zendesk_service._status_sync_trigger("01WEBHOOK")

    assert {c.get("value") for c in new_trigger["conditions"]["all"] if c["field"] == "update_type"} == {"Create"}
    assert {c.get("value") for c in status_email["conditions"]["all"] if c["field"] == "update_type"} == {"Change"}
    assert any(c["field"] == "status" and c["operator"] == "changed" for c in status_sync["conditions"]["all"])
    assert new_trigger["actions"][0]["field"] == "notification_target"
    assert status_sync["actions"][0]["field"] == "notification_webhook"
    assert '"status":"{{ticket.status}}"' in status_sync["actions"][0]["value"][1]


def test_status_reports_missing_environment(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'missing-env.db').as_posix()}",
        app_username="test-user",
        app_password="unit-test-password",
        frontend_url="https://portal.example.com",
    )
    app = create_app(settings)
    with TestClient(app) as client:
        client.auth = ("test-user", "unit-test-password")
        response = client.get("/api/zendesk/setup")
    app.state.engine.dispose()
    assert response.status_code == 200
    assert response.json()["environment_configured"] is False


def test_connect_validates_env_login_and_returns_dry_run_plan(monkeypatch, zendesk_app, zendesk_client):
    def fake_request(credentials, method, path, payload=None):
        assert credentials.subdomain == "example"
        assert credentials.email == "admin@example.com"
        assert credentials.token == "secret-token"
        assert method == "GET"
        assert path == "/api/v2/users/me.json"
        return {"user": {"id": 42, "name": "Zendesk Admin", "email": "admin@example.com", "role": "admin"}}

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    monkeypatch.setattr(
        zendesk_service,
        "build_setup_plan",
        lambda credentials, settings: [{
            "key": "brand", "object_type": "Brand", "name": "Royal Tyres",
            "action": "create", "existing_id": None, "details": None,
        }],
    )
    response = zendesk_client.post("/api/zendesk/connect")
    assert response.status_code == 200
    body = response.json()
    assert body["environment_configured"] is True
    assert body["workflow_environment_ready"] is True
    assert body["notification_email"] == "farhaanhotd1@gmail.com"
    assert body["connected"] is True
    assert body["can_configure"] is True
    assert len(body["plan_fingerprint"]) == 64


def test_apply_requires_explicit_confirmation(zendesk_client):
    response = zendesk_client.post(
        "/api/zendesk/apply",
        json={"confirm": False, "plan_fingerprint": "0" * 64},
    )
    assert response.status_code == 400


def test_apply_rejects_stale_reviewed_plan(monkeypatch, zendesk_app, zendesk_client):
    seed_configured_connection(zendesk_app)
    monkeypatch.setattr(zendesk_service, "build_setup_plan", lambda credentials, settings: [])
    response = zendesk_client.post(
        "/api/zendesk/apply",
        json={"confirm": True, "plan_fingerprint": "0" * 64},
    )
    assert response.status_code == 409


def test_apply_provisions_core_and_workflow_resources(monkeypatch, zendesk_app, zendesk_client):
    seed_configured_connection(zendesk_app)
    with zendesk_app.state.session_factory() as db:
        connection = db.get(ZendeskConnection, 1)
        for field in zendesk_service.ID_FIELDS:
            setattr(connection, field, None)
        db.commit()

    monkeypatch.setattr(zendesk_service, "_ensure_brand", lambda credentials: 201)
    monkeypatch.setattr(zendesk_service, "_ensure_group", lambda credentials: 202)
    field_ids = iter([203, 204, 205])
    monkeypatch.setattr(zendesk_service, "_ensure_field", lambda credentials, definition: next(field_ids))
    monkeypatch.setattr(zendesk_service, "_ensure_form", lambda credentials, brand_id, field_ids: 206)
    monkeypatch.setattr(zendesk_service, "_ensure_view", lambda credentials, group_id: 207)
    monkeypatch.setattr(zendesk_service, "_ensure_email_target", lambda credentials, settings: 208)
    monkeypatch.setattr(zendesk_service, "_ensure_webhook", lambda credentials, settings: "01WEBHOOK")
    trigger_ids = iter([209, 210, 211])
    monkeypatch.setattr(zendesk_service, "_ensure_trigger", lambda credentials, definition: next(trigger_ids))
    monkeypatch.setattr(
        zendesk_service,
        "_verify_object",
        lambda credentials, object_type, object_id, path, root_key: {
            "object_type": object_type, "id": object_id, "ok": True, "result": "PASS"
        },
    )
    monkeypatch.setattr(zendesk_service, "build_setup_plan", lambda credentials, settings: [])

    preview = zendesk_client.get("/api/zendesk/setup")
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
    assert len(body["verification"]) == 12
    assert all(item["ok"] for item in body["verification"])


def test_webhook_creation_uses_render_url_and_bearer_secret(monkeypatch, zendesk_app):
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", "secret-token")
    captured = {}
    monkeypatch.setattr(zendesk_service, "_list_webhooks", lambda credentials: [])

    def fake_request(credentials, method, path, payload=None):
        captured.update(method=method, path=path, payload=payload)
        return {"webhook": {"id": "01WEBHOOK"}}

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    assert zendesk_service._ensure_webhook(credentials, zendesk_app.state.settings) == "01WEBHOOK"
    webhook = captured["payload"]["webhook"]
    assert webhook["endpoint"] == "https://api.example.com/api/webhooks/zendesk"
    assert webhook["subscriptions"] == ["conditional_ticket_events"]
    assert webhook["authentication"]["type"] == "bearer_token"
    assert webhook["authentication"]["data"]["token"] == "webhook-unit-test-secret"


def test_successful_zendesk_create_updates_local_request(monkeypatch, zendesk_app, zendesk_client):
    seed_configured_connection(zendesk_app)
    monkeypatch.setattr(zendesk_service, "create_ticket", lambda settings, db, record: {"id": 98765, "status": "new"})
    response = zendesk_client.post("/api/requests", json=payload())
    assert response.status_code == 201
    body = response.json()
    assert body["zendesk_ticket_id"] == 98765
    assert body["zendesk_sync_status"] == "synced"
    assert audit_events(zendesk_app) == ["REQUEST_CREATED", "ZENDESK_TICKET_CREATED"]


def test_zendesk_failure_keeps_primary_request(monkeypatch, zendesk_app, zendesk_client):
    seed_configured_connection(zendesk_app)

    def fail_create(settings, db, record):
        from app.models.asset_request import AssetRequest

        # A separate connection must see the primary commit before the external
        # call fails; inspecting only the response would not prove this ordering.
        with zendesk_app.state.session_factory() as persisted:
            assert persisted.get(AssetRequest, record.id) is not None
            assert persisted.scalar(
                select(AuditLog.event_type).where(AuditLog.request_id == record.id)
            ) == "REQUEST_CREATED"
        raise zendesk_service.ZendeskError("simulated outage")

    monkeypatch.setattr(zendesk_service, "create_ticket", fail_create)
    response = zendesk_client.post("/api/requests", json=payload())
    assert response.status_code == 201
    body = response.json()
    assert body["zendesk_ticket_id"] is None
    assert body["zendesk_sync_status"] == "sync_failed"
    stored = zendesk_client.get(f"/api/requests/{body['id']}")
    assert stored.status_code == 200
    assert audit_events(zendesk_app) == ["REQUEST_CREATED", "ZENDESK_CREATE_FAILED"]
