"""
ROLE: Audit Repository: append persisted workflow history
CALLED BY: RequestService and WebhookService
CALLS: AuditLog and supplied Session
DATA IN: Request ID, event type, source and safe message
DATA OUT: Pending AuditLog entity for the service transaction
WHY: Centralize construction of audit records while services choose event timing.
SECURITY / RELIABILITY: No authentication/session state is stored here. Service commits the
    audit with its related state change.
FLOW: RequestService and WebhookService -> this module -> AuditLog and supplied Session
"""

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
