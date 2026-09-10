from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

AssetType = Literal["Laptop", "Monitor", "Mouse", "Keyboard", "Headset", "Docking Station", "Other"]


class AssetRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    requester_name: str = Field(min_length=2, max_length=100)
    requester_email: EmailStr = Field(max_length=254)
    asset_type: AssetType
    reason: str = Field(min_length=10, max_length=1000)


class AssetRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_name: str
    requester_email: str
    asset_type: str
    reason: str
    status: str
    zendesk_ticket_id: int | None
    zendesk_status: str | None
    zendesk_sync_status: str
    zendesk_last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
