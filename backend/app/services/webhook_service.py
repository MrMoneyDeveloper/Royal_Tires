import logging

from sqlalchemy.orm import Session

from app.data.base import utc_now
from app.helpers.request_identity import build_external_id
from app.models.asset_request import AssetRequest
from app.repositories import audit_repository, request_repository
from app.schemas.webhook_schema import ZendeskStatusWebhook

logger = logging.getLogger(__name__)


class WebhookRequestNotFound(Exception):
    pass


class WebhookIdentityMismatch(Exception):
    pass


def apply_zendesk_status(
    db: Session, event: ZendeskStatusWebhook
) -> tuple[AssetRequest, bool]:
    """Apply one authenticated Zendesk status event idempotently."""
    record = request_repository.get_by_zendesk_ticket_id(db, event.ticket_id)
    if record is None:
        raise WebhookRequestNotFound()

    if event.external_id and event.external_id != build_external_id(record.id):
        raise WebhookIdentityMismatch()

    changed = record.zendesk_status != event.status or record.status != event.status
    record.zendesk_status = event.status
    record.status = event.status
    record.zendesk_sync_status = "synced"
    record.zendesk_last_synced_at = utc_now()

    audit_repository.add_audit(
        db,
        record.id,
        "ZENDESK_STATUS_CHANGED" if changed else "ZENDESK_WEBHOOK_RECEIVED",
        "zendesk",
        (
            f"Zendesk ticket {event.ticket_id} status synced to {event.status}."
            if changed
            else f"Duplicate Zendesk status event received for ticket {event.ticket_id}."
        ),
    )
    db.commit()
    db.refresh(record)
    logger.info(
        "zendesk_status_sync request_id=%s ticket_id=%s status=%s changed=%s",
        record.id,
        event.ticket_id,
        event.status,
        changed,
    )
    return record, changed
