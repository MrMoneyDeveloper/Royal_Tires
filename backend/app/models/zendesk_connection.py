"""
ROLE: ZendeskConnection Model: singleton zendesk_connection table
CALLED BY: ZendeskService; metadata repository helpers
CALLS: Declarative Base and SQLAlchemy columns
DATA IN: Safe account metadata, managed IDs and verification timestamps
DATA OUT: Persisted singleton metadata, conventionally id=1
WHY: Reuse verified integration IDs without storing credentials in SQL.
SECURITY / RELIABILITY: id is the local primary key. Brand/group/field/form/view IDs come from
    Zendesk, not local foreign keys. API token remains in server configuration.
FLOW: ZendeskService; metadata repository helpers -> this module -> Declarative Base and
    SQLAlchemy columns
"""

from datetime import datetime

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.data.base import Base, UTCDateTime, utc_now


class ZendeskConnection(Base):
    """Singleton record for verified Zendesk metadata and managed object IDs."""

    __tablename__ = "zendesk_connection"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    subdomain: Mapped[str] = mapped_column(String(100))
    api_email: Mapped[str] = mapped_column(String(254))

    connected_user_name: Mapped[str | None] = mapped_column(String(150))
    connected_user_email: Mapped[str | None] = mapped_column(String(254))
    connected_user_role: Mapped[str | None] = mapped_column(String(40))

    # ZendeskService stores discovered remote IDs here for ticket creation; these are not local foreign keys.
    brand_id: Mapped[int | None] = mapped_column(BigInteger)
    group_id: Mapped[int | None] = mapped_column(BigInteger)
    ticket_form_id: Mapped[int | None] = mapped_column(BigInteger)
    asset_type_field_id: Mapped[int | None] = mapped_column(BigInteger)
    local_request_id_field_id: Mapped[int | None] = mapped_column(BigInteger)
    request_source_field_id: Mapped[int | None] = mapped_column(BigInteger)
    view_id: Mapped[int | None] = mapped_column(BigInteger)

    connected_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now)
    configured_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
