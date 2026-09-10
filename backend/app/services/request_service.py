"""
ROLE: Request Service: business sequencing and transaction ownership
CALLED BY: Request Controller
CALLS: RequestRepository, AuditRepository, AssetRequest and ZendeskService
DATA IN: Validated request, injected Session and Settings
DATA OUT: Committed primary request, audit history and integration state
WHY: Service decides why and when persistence happens; repositories decide how.
SECURITY / RELIABILITY: Flush obtains the local ID; commit saves request plus REQUEST_CREATED
    before Zendesk. Expected ZendeskError leaves the request saved and records sync_failed; no
    automatic retry is implemented.
FLOW: Request Controller -> this module -> RequestRepository, AuditRepository, AssetRequest
    and ZendeskService
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.data.base import utc_now
from app.models.asset_request import AssetRequest
from app.repositories import audit_repository, request_repository
from app.schemas.request_schema import AssetRequestCreate
from app.services import zendesk_service

logger = logging.getLogger(__name__)


class RequestNotFound(Exception):
    pass


def add_audit(
    db: Session,
    request_id: int,
    event_type: str,
    source: str,
    message: str,
) -> None:
    # repositories/audit_repository.py stages an AuditLog in this transaction; this Service chooses the event timing.
    audit_repository.add_audit(db, request_id, event_type, source, message)
    logger.info("event=%s request_id=%s source=%s", event_type, request_id, source)


def create_request(
    db: Session, data: AssetRequestCreate, settings: Settings
) -> AssetRequest:
    # Convert the validated DTO from request_schema.py into the persisted Model in models/asset_request.py.
    record = AssetRequest(**data.model_dump())
    # repositories/request_repository.py stages the Model using our injected Session; it does not commit.
    request_repository.add_request(db, record)
    # Flush through the Data Session to obtain the database ID for AuditLog; the request is not committed yet.
    db.flush()
    add_audit(db, record.id, "REQUEST_CREATED", "api", "Asset request saved.")

    # PostgreSQL/SQLite is the primary system of record. Commit before calling
    # Zendesk so a helpdesk outage can never discard the employee request.
    db.commit()
    db.refresh(record)

    # zendesk_service.py reads saved configuration via zendesk_repository.py before attempting external HTTP.
    if not zendesk_service.is_configured(db):
        return record

    try:
        # zendesk_service.py calls Zendesk only after the local commit; its result carries the external ticket ID.
        ticket = zendesk_service.create_ticket(settings, db, record)
        # Attach Zendesk's ID to the already-saved Model; the local database primary key stays unchanged.
        record.zendesk_ticket_id = ticket["id"]
        record.zendesk_status = ticket.get("status") or "new"
        record.zendesk_sync_status = "synced"
        record.zendesk_last_synced_at = utc_now()
        add_audit(
            db,
            record.id,
            "ZENDESK_TICKET_CREATED",
            "zendesk",
            f"Zendesk ticket {record.zendesk_ticket_id} created from verified portal configuration.",
        )
    except zendesk_service.ZendeskError:
        logger.exception("Zendesk ticket creation failed request_id=%s", record.id)
        record.zendesk_sync_status = "sync_failed"
        add_audit(
            db,
            record.id,
            "ZENDESK_CREATE_FAILED",
            "zendesk",
            "Zendesk ticket creation failed; local request remains saved.",
        )

    # Commit integration outcome and audit together; Zendesk failure cannot undo the earlier primary commit.
    db.commit()
    db.refresh(record)
    return record


def get_request(db: Session, request_id: int) -> AssetRequest:
    # request_repository.py returns a Model or None; the Service decides that a missing request is an error.
    record = request_repository.get_request(db, request_id)
    if record is None:
        raise RequestNotFound()
    return record


def list_requests(db: Session, limit: int, offset: int) -> list[AssetRequest]:
    # request_repository.py owns the ordered ORM query; the Controller receives the resulting Models.
    return request_repository.list_requests(db, limit, offset)
