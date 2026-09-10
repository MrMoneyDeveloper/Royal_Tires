import pytest
from sqlalchemy import select

from app.models.asset_request import AssetRequest
from app.models.audit_log import AuditLog


def test_create_persists_request_and_audit(client, app, request_payload):
    response = client.post("/api/requests", json=request_payload)

    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["status"] == "new"
    assert created["zendesk_sync_status"] == "sync_pending"
    assert created["zendesk_ticket_id"] is None
    assert created["created_at"]
    assert created["updated_at"]

    # A fresh session proves the API committed both records to the database.
    with app.state.session_factory() as session:
        saved = session.get(AssetRequest, created["id"])
        assert saved is not None
        for field, expected in request_payload.items():
            assert getattr(saved, field) == expected
        audit = session.scalars(
            select(AuditLog).where(AuditLog.request_id == saved.id)
        ).all()
        assert len(audit) == 1
        assert audit[0].event_type == "REQUEST_CREATED"


def test_list_and_detail_return_saved_requests(client, request_payload):
    first = client.post("/api/requests", json=request_payload).json()
    second = client.post(
        "/api/requests", json={**request_payload, "asset_type": "Monitor"}
    ).json()

    detail = client.get(f"/api/requests/{first['id']}")
    assert detail.status_code == 200
    assert detail.json() == first

    listing = client.get("/api/requests")
    assert listing.status_code == 200
    assert {item["id"] for item in listing.json()} == {first["id"], second["id"]}
    first_page = client.get("/api/requests?limit=1&offset=0").json()
    second_page = client.get("/api/requests?limit=1&offset=1").json()
    assert len(first_page) == len(second_page) == 1
    assert first_page[0]["id"] != second_page[0]["id"]
    assert client.get("/api/requests?offset=2").json() == []


def test_missing_request_returns_404(client):
    assert client.get("/api/requests/999999").status_code == 404


def test_text_fields_are_trimmed(client, request_payload):
    response = client.post(
        "/api/requests",
        json={
            **request_payload,
            "requester_name": "  Mohammed Buckas  ",
            "reason": "  Replacement laptop required for development work.  ",
        },
    )
    assert response.status_code == 201
    assert response.json()["requester_name"] == request_payload["requester_name"]
    assert response.json()["reason"] == request_payload["reason"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("requester_name", "A"),
        ("requester_name", " " * 10),
        ("requester_name", "A" * 101),
        ("requester_email", "not-an-email"),
        ("asset_type", "Server"),
        ("reason", "Too short"),
        ("reason", " " * 20),
        ("reason", "x" * 1001),
    ],
)
def test_invalid_input_is_rejected_without_persistence(
    client, app, request_payload, field, value
):
    response = client.post(
        "/api/requests", json={**request_payload, field: value}
    )
    assert response.status_code == 422
    with app.state.session_factory() as session:
        assert session.scalars(select(AssetRequest)).all() == []
        assert session.scalars(select(AuditLog)).all() == []


def test_missing_reason_is_rejected(client, request_payload):
    del request_payload["reason"]
    assert client.post("/api/requests", json=request_payload).status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_invalid_pagination_is_rejected(client, query):
    assert client.get(f"/api/requests?{query}").status_code == 422
