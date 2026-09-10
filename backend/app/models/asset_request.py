"""
ROLE: AssetRequest Model: asset_requests SQL table
CALLED BY: RequestService constructs; repositories and Data persist/query
CALLS: Declarative Base and SQLAlchemy column mapping
DATA IN: Requester, asset, reason and integration state
DATA OUT: Persisted primary request entity
WHY: Define the system-of-record representation independently of API DTOs.
SECURITY / RELIABILITY: Database-generated id is the primary key. Nullable unique
    zendesk_ticket_id is an external identifier, not a local foreign key. Hosted storage is
    PostgreSQL; SQLite is for local/test use.
FLOW: RequestService constructs; repositories and Data persist/query -> this module ->
    Declarative Base and SQLAlchemy column mapping
"""

from datetime import datetime

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.data.base import Base, UTCDateTime, utc_now


class AssetRequest(Base):
    __tablename__ = "asset_requests"

    # SQLAlchemy maps these attributes to asset_requests columns; the database generates this local primary key.
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_name: Mapped[str] = mapped_column(String(100))
    requester_email: Mapped[str] = mapped_column(String(254))
    asset_type: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    # ZendeskService supplies this external ID after creation; it is not a foreign key to a local table.
    zendesk_ticket_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    zendesk_status: Mapped[str | None] = mapped_column(String(20))
    zendesk_sync_status: Mapped[str] = mapped_column(String(20), default="sync_pending")
    zendesk_last_synced_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, onupdate=utc_now)
