import pytest
from pydantic import SecretStr


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/api/requests"), ("get", "/api/requests/1"), ("post", "/api/requests")],
)
def test_business_routes_require_basic_auth(client, request_payload, method, path):
    response = client.request(method, path, json=request_payload, auth=None)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")


@pytest.mark.parametrize(
    "credentials",
    [("test-user", "wrong-password"), ("wrong-user", "unit-test-password")],
)
def test_bad_credentials_are_rejected(client, credentials):
    response = client.get("/api/requests", auth=credentials)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic")
    assert credentials[0] not in response.text
    assert credentials[1] not in response.text


def test_malformed_authorization_is_rejected(client):
    response = client.get(
        "/api/requests", auth=None, headers={"Authorization": "Basic invalid!"}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("field", ["app_username", "app_password"])
def test_missing_demo_configuration_fails_closed(client, app, field):
    setattr(app.state.settings, field, SecretStr("") if field == "app_password" else "")
    assert client.get("/api/requests").status_code == 503
    assert client.get("/health", auth=None).status_code == 200


def test_health_and_documentation_are_public(client):
    for path in ["/health", "/docs", "/openapi.json"]:
        assert client.get(path, auth=None).status_code == 200


def test_swagger_exposes_basic_auth_for_business_routes(client):
    schema = client.get("/openapi.json", auth=None).json()
    schemes = schema["components"]["securitySchemes"]
    basic_names = {
        name for name, scheme in schemes.items()
        if scheme.get("type") == "http" and scheme.get("scheme") == "basic"
    }
    assert basic_names
    for path, method in [
        ("/api/requests", "get"),
        ("/api/requests", "post"),
        ("/api/requests/{request_id}", "get"),
    ]:
        security = schema["paths"][path][method]["security"]
        assert any(set(requirement) & basic_names for requirement in security)
    assert not schema["paths"]["/health"]["get"].get("security")
