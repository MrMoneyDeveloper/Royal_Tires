import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import utc_now
from app.models.asset_request import AssetRequest
from app.models.audit_log import AuditLog
from app.schemas import ZendeskStatusWebhook

logger = logging.getLogger(__name__)


class WebhookRequestNotFound(Exception):
    pass


class WebhookIdentityMismatch(Exception):
    pass


def apply_zendesk_status(db: Session, event: ZendeskStatusWebhook) -> tuple[AssetRequest, bool]:
    """Apply one authenticated Zendesk status event idempotently."""
    record = db.scalar(
        select(AssetRequest).where(AssetRequest.zendesk_ticket_id == event.ticket_id)
    )
    if record is None:
        raise WebhookRequestNotFound()

    expected_external_id = f"royal-tires-asset-{record.id}"
    if event.external_id and event.external_id != expected_external_id:
        raise WebhookIdentityMismatch()

    changed = record.zendesk_status != event.status or record.status != event.status
    record.zendesk_status = event.status
    record.status = event.status
    record.zendesk_sync_status = "synced"
    record.zendesk_last_synced_at = utc_now()

    db.add(
        AuditLog(
            request_id=record.id,
            event_type=("ZENDESK_STATUS_CHANGED" if changed else "ZENDESK_WEBHOOK_RECEIVED"),
            source="zendesk",
            message=(
                f"Zendesk ticket {event.ticket_id} status synced to {event.status}."
                if changed
                else f"Duplicate Zendesk status event received for ticket {event.ticket_id}."
            ),
        )
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
