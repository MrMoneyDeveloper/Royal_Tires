"""
ROLE: Webhook Schemas: event and acknowledgement contracts
CALLED BY: FastAPI Webhook Controller
CALLS: Pydantic literals and constraints
DATA IN: Event, positive ticket ID, optional external ID and status
DATA OUT: Typed event or validation error; acknowledgement fields
WHY: Validate external event shape before business processing.
SECURITY / RELIABILITY: Rejects extra fields and unsupported statuses. External ID is optional
    in this contract; WebhookService checks it when supplied. Schema validation does not
    replace bearer authentication.
FLOW: FastAPI Webhook Controller -> this module -> Pydantic literals and constraints
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ZendeskTicketStatus = Literal["new", "open", "pending", "hold", "solved", "closed"]


class ZendeskStatusWebhook(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    event: Literal["status_changed"] = "status_changed"
    ticket_id: int = Field(gt=0)
    external_id: str | None = Field(default=None, max_length=150)
    status: ZendeskTicketStatus


class ZendeskWebhookResponse(BaseModel):
    ok: bool
    request_id: int
    zendesk_ticket_id: int
    status: str
    changed: bool
