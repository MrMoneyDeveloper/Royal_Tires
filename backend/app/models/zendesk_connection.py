from datetime import datetime

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, UTCDateTime, utc_now


class ZendeskConnection(Base):
    """Singleton Zendesk connection/configuration record for the demo portal."""

    __tablename__ = "zendesk_connection"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    subdomain: Mapped[str] = mapped_column(String(100))
    api_email: Mapped[str] = mapped_column(String(254))
    encrypted_api_token: Mapped[str] = mapped_column(Text)

    connected_user_name: Mapped[str | None] = mapped_column(String(150))
    connected_user_email: Mapped[str | None] = mapped_column(String(254))
    connected_user_role: Mapped[str | None] = mapped_column(String(40))

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
