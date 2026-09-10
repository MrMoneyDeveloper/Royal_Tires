"""
ROLE: AuditLog Model: audit_logs SQL table
CALLED BY: AuditRepository
CALLS: Declarative Base; foreign key to asset_requests.id
DATA IN: Event type/source/message/time and request_id
DATA OUT: Persisted chronological workflow history in PostgreSQL
WHY: One AssetRequest can have many audit events for diagnosis and explanation.
SECURITY / RELIABILITY: id is the audit primary key. request_id is the foreign key linking the
    event to AssetRequest. AuditLog is NOT authentication or browser-session state; no ORM
    relationship property is required to enforce the SQL foreign key.
FLOW: AuditRepository -> this module -> Declarative Base; foreign key to asset_requests.id
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.base import Base, UTCDateTime, utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Link this audit row to models/asset_request.py; one request can have many persisted workflow events.
    request_id: Mapped[int] = mapped_column(ForeignKey("asset_requests.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
