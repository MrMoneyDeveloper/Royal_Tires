"""
ROLE: Request Repository: ORM persistence operations
CALLED BY: RequestService and WebhookService
CALLS: AssetRequest and the supplied SQLAlchemy Session
DATA IN: Session, entity, local/ticket ID or pagination
DATA OUT: Added entity, matching entity or ordered list
WHY: Encapsulate how add/get/list/ticket lookup are performed.
SECURITY / RELIABILITY: Receives a Session; does not open its own Internet connection or
    commit. ORM values are bound parameters, not interpolated SQL.
FLOW: RequestService and WebhookService -> this module -> AssetRequest and the supplied
    SQLAlchemy Session
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_request import AssetRequest


def add_request(db: Session, record: AssetRequest) -> None:
    # Stage models/asset_request.py in the supplied Session; request_service.py owns flush/commit timing.
    db.add(record)


def get_request(db: Session, request_id: int) -> AssetRequest | None:
    # SQLAlchemy resolves the Model by primary key and returns it or None; caller decides missing-record behavior.
    return db.get(AssetRequest, request_id)


def list_requests(db: Session, limit: int, offset: int) -> list[AssetRequest]:
    statement = select(AssetRequest).order_by(
        AssetRequest.created_at.desc(),
        AssetRequest.id.desc(),
    )
    # Execute through data/session.py's injected Session; return Models rather than HTTP response objects.
    return list(db.scalars(statement.limit(limit).offset(offset)))


def get_by_zendesk_ticket_id(
    db: Session, zendesk_ticket_id: int
) -> AssetRequest | None:
    # Bind the external ticket ID as SQL data; webhook_service.py uses the matching Model for correlation.
    statement = select(AssetRequest).where(
        AssetRequest.zendesk_ticket_id == zendesk_ticket_id
    )
    return db.scalar(statement)
