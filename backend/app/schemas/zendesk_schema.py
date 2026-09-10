"""
ROLE: Setup Schemas: approval and safe response contracts
CALLED BY: FastAPI Zendesk Controller
CALLS: Pydantic types, patterns and action literals
DATA IN: Confirmation/fingerprint or safe setup result
DATA OUT: Validated apply input and bounded response structure
WHY: Specify the browser/backend contract without exposing integration credentials.
SECURITY / RELIABILITY: Apply forbids extra fields and requires a 64-character lowercase hex
    fingerprint; confirmation itself is checked by the controller. Models persist data; these
    schemas describe HTTP data.
FLOW: FastAPI Zendesk Controller -> this module -> Pydantic types, patterns and action
    literals
"""

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
