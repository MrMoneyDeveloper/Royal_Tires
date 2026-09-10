import base64

import httpx
import pytest

from app.services import zendesk_service


def test_record_invalid_includes_nested_field_validation():
    response = httpx.Response(422, json={
        "error": "RecordInvalid",
        "description": "Record validation errors",
        "details": {"base": [
            {"description": "The tag <strong>other</strong> is already used in a custom field drop-down, multi-select or checkbox.", "value": "private input"},
        ]},
    })
    detail = zendesk_service._safe_zendesk_error(response)
    assert "base: The tag <strong>other</strong> is already used" in detail
    assert "private input" not in detail


def test_gateway_error_and_logs_exclude_authentication_and_payload_secrets(monkeypatch, caplog):
    token = "private-api-token"
    webhook_secret = "private-webhook-secret"
    credentials = zendesk_service.ZendeskCredentials("example", "admin@example.com", token)
    basic_value = base64.b64encode(f"admin@example.com/token:{token}".encode()).decode()
    response = httpx.Response(422, json={
        "error": "RecordInvalid",
        "description": f"Invalid {token} and Basic {basic_value}",
        "details": {
            "authentication": [{"description": f"Rejected {webhook_secret}", "value": "raw private body"}],
            "password": "hidden-password",
        },
        "request": {"Authorization": basic_value},
    })
    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: response)
    with pytest.raises(zendesk_service.ZendeskError) as caught:
        zendesk_service._request_json(credentials, "POST", "/api/v2/webhooks", {
            "webhook": {"authentication": {"data": {"token": webhook_secret}}},
        })
    assert caught.value.status_code == 502
    combined = str(caught.value) + caplog.text
    assert "authentication: Rejected [redacted]" in combined
    for secret in (token, webhook_secret, basic_value, "hidden-password", "raw private body"):
        assert secret not in combined


@pytest.mark.parametrize("response", [httpx.Response(502, text="<html>private error</html>"), httpx.Response(422, json=["private error"])])
def test_non_object_error_bodies_are_not_returned(response):
    assert zendesk_service._safe_zendesk_error(response) == ""


def test_validation_detail_is_bounded_and_cannot_inject_log_lines():
    response = httpx.Response(422, json={"details": {"Title": [{"description": "Bad\nvalue " + "x" * 1000}]}})
    detail = zendesk_service._safe_zendesk_error(response)
    assert detail.startswith("Title: Bad value")
    assert "\n" not in detail
    assert len(detail) <= 600
