from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ZendeskApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool
    plan_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")


class ZendeskPlanItem(BaseModel):
    key: str
    object_type: str
    name: str
    action: Literal["create", "reuse", "update", "skip"]
    existing_id: int | str | None = None
    details: str | None = None


class ZendeskUserSummary(BaseModel):
    name: str | None = None
    email: str | None = None
    role: str | None = None


class ZendeskSetupStatus(BaseModel):
    environment_configured: bool = False
    workflow_environment_ready: bool = False
    notification_email: str | None = None
    connected: bool
    configured: bool
    can_configure: bool
    instance: str | None = None
    user: ZendeskUserSummary | None = None
    plan: list[ZendeskPlanItem] = []
    plan_fingerprint: str | None = None
    ids: dict[str, int | None] | None = None
    verification: list[dict[str, str | int | bool | None]] = []
    message: str = ""
