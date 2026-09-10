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
