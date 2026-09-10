"""
ROLE: Request/response Schemas: Pydantic DTO contracts
CALLED BY: FastAPI Request Controller
CALLS: Pydantic field checks and reason validator
DATA IN: Untrusted request JSON; response ORM attributes
DATA OUT: Validated AssetRequestCreate or serialized AssetRequestResponse
WHY: Separate API validation from persisted database representation.
SECURITY / RELIABILITY: Rejects extra fields, invalid email/assets/lengths. Reason must
    contain 10 non-whitespace characters; valid formatting is preserved. A schema is not a
    database table.
FLOW: FastAPI Request Controller -> this module -> Pydantic field checks and reason validator
"""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

AssetType = Literal[
    "Laptop",
    "Monitor",
    "Mouse",
    "Keyboard",
    "Headset",
    "Docking Station",
    "Other",
]


class AssetRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    requester_name: str = Field(min_length=2, max_length=100)
    requester_email: EmailStr = Field(max_length=254)
    asset_type: AssetType
    reason: str = Field(min_length=10, max_length=1000)

    @field_validator("reason")
    @classmethod
    def require_meaningful_reason(cls, value: str) -> str:
        # Whitespace can improve readability, but it must not satisfy the
        # minimum business-context requirement by itself.
        if len(re.sub(r"\s", "", value)) < 10:
            raise ValueError(
                "Business reason must contain at least 10 non-whitespace characters."
            )
        return value


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
