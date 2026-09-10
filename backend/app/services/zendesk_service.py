import re

import httpx

from app.core.config import Settings
from app.models.asset_request import AssetRequest

_SUBDOMAIN = re.compile(r"^[A-Za-z0-9-]+$")


class ZendeskError(Exception):
    """Raised when a Zendesk ticket cannot be created safely."""


def is_configured(settings: Settings) -> bool:
    return bool(
        settings.zendesk_subdomain
        and settings.zendesk_email
        and settings.zendesk_api_token.get_secret_value()
    )


def create_ticket(settings: Settings, record: AssetRequest) -> dict:
    """Create one Zendesk ticket linked to the durable local asset request."""
    if not is_configured(settings):
        raise ZendeskError("Zendesk integration is not configured.")
    if not _SUBDOMAIN.fullmatch(settings.zendesk_subdomain):
        raise ZendeskError("Zendesk subdomain is invalid.")

    url = f"https://{settings.zendesk_subdomain}.zendesk.com/api/v2/tickets.json"
    token = settings.zendesk_api_token.get_secret_value()
    payload = {
        "ticket": {
            "subject": f"IT Asset Request #{record.id} - {record.asset_type} - {record.requester_name}",
            "comment": {
                "body": (
                    f"IT asset request #{record.id}\n\n"
                    f"Asset: {record.asset_type}\n"
                    f"Requester: {record.requester_name} <{record.requester_email}>\n\n"
                    f"Business reason:\n{record.reason}"
                ),
                "public": False,
            },
            "requester": {
                "name": record.requester_name,
                "email": record.requester_email,
            },
            "external_id": f"royal-tires-asset-{record.id}",
            "tags": [
                "it_asset_request",
                "royal_tires_asset_portal",
                f"local_request_{record.id}",
            ],
            "priority": "normal",
        }
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            auth=(f"{settings.zendesk_email}/token", token),
            timeout=10.0,
            headers={"User-Agent": "RoyalTyresAssetPortal/0.1"},
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ZendeskError("Zendesk ticket creation failed.") from exc

    ticket = data.get("ticket") if isinstance(data, dict) else None
    if not isinstance(ticket, dict) or not isinstance(ticket.get("id"), int):
        raise ZendeskError("Zendesk returned an invalid ticket response.")
    return ticket
