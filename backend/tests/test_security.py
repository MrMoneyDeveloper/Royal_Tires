import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.models.asset_request import AssetRequest
from app.services import request_service


@pytest.mark.parametrize("origin", ["http://localhost:5173", "https://portal.example.com"])
def test_configured_origins_allow_authenticated_preflight(client, origin):
    response = client.options(
        "/api/requests",
        auth=None,
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_unconfigured_origin_is_rejected(client):
    response = client.options(
        "/api/requests",
        auth=None,
        headers={
            "Origin": "https://portal.example.com.attacker.invalid",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_sql_injection_text_is_stored_as_data(client, app, request_payload):
    reason = "'); DROP TABLE asset_requests; --"
    response = client.post("/api/requests", json={**request_payload, "reason": reason})
    assert response.status_code == 201
    assert response.json()["reason"] == reason
    assert client.post("/api/requests", json=request_payload).status_code == 201
    with app.state.session_factory() as session:
        saved = session.scalars(select(AssetRequest).order_by(AssetRequest.id)).all()
        assert len(saved) == 2
        assert saved[0].reason == reason


def test_validation_errors_omit_raw_input(client, request_payload):
    private_reason = "s3cr3t"
    response = client.post(
        "/api/requests", json={**request_payload, "reason": private_reason}
    )
    assert response.status_code == 422
    assert private_reason not in response.text
    errors = response.json()["detail"]
    assert errors
    assert all("input" not in error and "ctx" not in error for error in errors)


def test_unexpected_error_response_is_generic(app, request_payload, monkeypatch):
    private_error = "private-database-password"

    def fail_create(*args, **kwargs):
        raise RuntimeError(private_error)

    monkeypatch.setattr(request_service, "create_request", fail_create)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/requests",
            json=request_payload,
            auth=("test-user", "unit-test-password"),
        )
    assert response.status_code == 500
    assert response.json()["detail"]
    assert private_error not in response.text
    assert "traceback" not in response.text.lower()
