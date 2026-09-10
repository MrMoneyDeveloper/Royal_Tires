import logging

from sqlalchemy.orm import Session

from app import repository
from app.models.asset_request import AssetRequest
from app.models.audit_log import AuditLog
from app.schemas import AssetRequestCreate

logger = logging.getLogger(__name__)


class RequestNotFound(Exception):
    pass


def add_audit(db: Session, request_id: int, event_type: str, source: str, message: str) -> None:
    db.add(AuditLog(request_id=request_id, event_type=event_type, source=source, message=message))
    logger.info("event=%s request_id=%s source=%s", event_type, request_id, source)


def create_request(db: Session, data: AssetRequestCreate) -> AssetRequest:
    record = AssetRequest(**data.model_dump())
    db.add(record)
    db.flush()
    add_audit(db, record.id, "REQUEST_CREATED", "api", "Asset request saved.")
    # The request and its audit event are durable before any secondary integration.
    db.commit()
    db.refresh(record)
    return record


def get_request(db: Session, request_id: int) -> AssetRequest:
    record = repository.get_request(db, request_id)
    if record is None:
        raise RequestNotFound()
    return record


def list_requests(db: Session, limit: int, offset: int) -> list[AssetRequest]:
    return repository.list_requests(db, limit, offset)
