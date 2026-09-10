from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def add_audit(
    db: Session,
    request_id: int,
    event_type: str,
    source: str,
    message: str,
) -> AuditLog:
    event = AuditLog(
        request_id=request_id,
        event_type=event_type,
        source=source,
        message=message,
    )
    db.add(event)
    return event
