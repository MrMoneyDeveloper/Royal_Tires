"""
ROLE: Webhook Controller: inbound status HTTP boundary
CALLED BY: Zendesk webhook POST /api/webhooks/zendesk
CALLS: WebhookService, webhook schemas and get_db
DATA IN: JSON ticket/status identity plus Authorization header
DATA OUT: Acknowledgement or 401/404/409/503 error
WHY: Keep authentication and HTTP error translation outside status persistence.
SECURITY / RELIABILITY: Uses its own bearer secret with constant-time comparison, not portal
    Basic Auth. Never log the header.
FLOW: Zendesk webhook POST /api/webhooks/zendesk -> this module -> WebhookService, webhook
    schemas and get_db
"""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.data.session import get_db
from app.schemas.webhook_schema import ZendeskStatusWebhook, ZendeskWebhookResponse
from app.services import webhook_service

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])
Database = Annotated[Session, Depends(get_db)]


def _require_zendesk_bearer(request: Request, authorization: str | None) -> None:
    expected = request.app.state.settings.zendesk_webhook_secret.get_secret_value().strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Zendesk webhook secret is not configured.",
        )
    scheme, _, token = (authorization or "").partition(" ")
    if (
        scheme.lower() != "bearer"
        or not token
        or not hmac.compare_digest(token, expected)
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook authentication.")


@router.post("/zendesk", response_model=ZendeskWebhookResponse)
def zendesk_status_webhook(
    payload: ZendeskStatusWebhook,
    db: Database,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
):
    _require_zendesk_bearer(request, authorization)
    try:
        record, changed = webhook_service.apply_zendesk_status(db, payload)
    except webhook_service.WebhookRequestNotFound as exc:
        raise HTTPException(
            status_code=404,
            detail="Linked asset request was not found.",
        ) from exc
    except webhook_service.WebhookIdentityMismatch as exc:
        raise HTTPException(
            status_code=409,
            detail="Zendesk ticket identity did not match the local request.",
        ) from exc

    return {
        "ok": True,
        "request_id": record.id,
        "zendesk_ticket_id": payload.ticket_id,
        "status": payload.status,
        "changed": changed,
    }
