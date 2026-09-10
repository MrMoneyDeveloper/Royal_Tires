from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

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


class ZendeskConnectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subdomain: str = Field(min_length=1, max_length=150)
    email: EmailStr = Field(max_length=254)
    api_token: SecretStr = Field(min_length=1)


class ZendeskApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool


class ZendeskPlanItem(BaseModel):
    key: str
    object_type: str
    name: str
    action: Literal["create", "reuse"]
    existing_id: int | None = None


class ZendeskUserSummary(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None


class ZendeskSetupStatus(BaseModel):
    connected: bool
    configured: bool
    can_configure: bool
    instance: str | None = None
    user: ZendeskUserSummary | None = None
    plan: list[ZendeskPlanItem] = []
    ids: dict[str, int | None] | None = None
    verification: list[dict[str, str | int | bool | None]] = []
    message: str = ""
