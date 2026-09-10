import json
import logging
import re
import base64
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database import utc_now
from app.models.asset_request import AssetRequest
from app.models.zendesk_connection import ZendeskConnection

logger = logging.getLogger(__name__)

_SUBDOMAIN = re.compile(r"^[a-z0-9][a-z0-9-]{0,98}[a-z0-9]$|^[a-z0-9]$")

BRAND_NAME = "Royal Tyres"
GROUP_NAME = "Royal Tyres | IT Service Desk"
FORM_NAME = "Royal Tyres | IT Asset Request"
VIEW_NAME = "Royal Tyres | IT Asset Requests"
PORTAL_TAG = "royal_tires_asset_portal"

EMAIL_TARGET_NAME = "Royal Tyres | Demo Notifications"
WEBHOOK_NAME = "Royal Tyres | Asset Status Sync"
TRIGGER_NEW_EMAIL_NAME = "Royal Tyres | Notify Demo Receiver - New Request"
TRIGGER_STATUS_EMAIL_NAME = "Royal Tyres | Notify Demo Receiver - Status Update"
TRIGGER_STATUS_SYNC_NAME = "Royal Tyres | Sync Status to Asset Portal"
EMAIL_TARGET_SUBJECT = "[Royal Tyres IT] Asset request update"

# Zendesk calls a single-select dropdown a `tagger` in the Ticket Fields API.
FIELD_DEFINITIONS = {
    "asset_type_field": {
        "title": "RT | Asset Type",
        "type": "tagger",
        "custom_field_options": [
            {"name": "Laptop", "value": "laptop"},
            {"name": "Monitor", "value": "monitor"},
            {"name": "Mouse", "value": "mouse"},
            {"name": "Keyboard", "value": "keyboard"},
            {"name": "Headset", "value": "headset"},
            {"name": "Docking Station", "value": "docking_station"},
            {"name": "Other", "value": "other"},
        ],
    },
    "local_request_id_field": {
        "title": "RT | Local Request ID",
        "type": "text",
    },
    "request_source_field": {
        "title": "RT | Request Source",
        "type": "tagger",
        "custom_field_options": [
            {"name": "Royal Tyres Asset Portal", "value": PORTAL_TAG},
        ],
    },
}

ID_FIELDS = (
    "brand_id",
    "group_id",
    "ticket_form_id",
    "asset_type_field_id",
    "local_request_id_field_id",
    "request_source_field_id",
    "view_id",
)


class ZendeskError(Exception):
    """Safe error returned for Zendesk connection/configuration failures."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ZendeskCredentials:
    subdomain: str
    email: str
    token: str


def normalize_subdomain(value: str) -> str:
    raw = value.strip().lower()
    if raw.startswith(("https://", "http://")):
        parsed = urlsplit(raw)
        raw = parsed.hostname or ""
    raw = raw.rstrip("/")
    if raw.endswith(".zendesk.com"):
        raw = raw[: -len(".zendesk.com")]
    if not _SUBDOMAIN.fullmatch(raw):
        raise ZendeskError(
            "ZENDESK_SUBDOMAIN must be a valid Zendesk subdomain such as 'digify7'.",
            503,
        )
    return raw


def _credentials_from_settings(settings: Settings) -> ZendeskCredentials:
    subdomain = settings.zendesk_subdomain.strip()
    email = settings.zendesk_email.strip()
    token = settings.zendesk_api_token.get_secret_value().strip()
    if not subdomain or not email or not token:
        raise ZendeskError(
            "Zendesk environment variables are incomplete. Configure ZENDESK_SUBDOMAIN, ZENDESK_EMAIL and ZENDESK_API_TOKEN on Render.",
            503,
        )
    return ZendeskCredentials(normalize_subdomain(subdomain), email, token)


def _safe_zendesk_error(response: httpx.Response, sensitive_values: tuple[str, ...] = ()) -> str:
    """Expose validation messages, excluding raw values and known request secrets."""
    try:
        data = response.json()
    except ValueError:
        return ""
    if not isinstance(data, dict):
        return ""

    parts: list[str] = []
    for key in ("error", "description"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
        elif isinstance(value, dict):
            for nested_key in ("title", "message", "description"):
                nested = value.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    parts.append(nested.strip())

    # RecordInvalid puts the useful reason under details.<field>[].description.
    # Reading only message keys prevents input/value/authentication objects from
    # being serialized wholesale into the browser response or application log.
    details = data.get("details")
    if isinstance(details, dict):
        for field, errors in list(details.items())[:8]:
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.\[\]-]{0,79}", field):
                continue
            if field.lower() in {"token", "password", "secret", "authorization", "input", "value"}:
                continue
            entries = errors if isinstance(errors, list) else [errors]
            for entry in entries[:3]:
                if isinstance(entry, str):
                    parts.append(f"{field}: {entry}")
                elif isinstance(entry, dict):
                    for key in ("description", "message", "title"):
                        message = entry.get(key)
                        if isinstance(message, str) and message.strip():
                            parts.append(f"{field}: {message.strip()}")

    detail = " | ".join(dict.fromkeys(parts))
    for value in sorted(filter(None, sensitive_values), key=len, reverse=True):
        detail = detail.replace(value, "[redacted]")
    detail = re.sub(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9+/=_\-.]+", r"\1 [redacted]", detail)
    return " ".join(detail.split())[:600]


def _payload_secrets(payload) -> tuple[str, ...]:
    """Keep any webhook authentication value out of upstream error messages."""
    values = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() in {"token", "password", "secret", "authorization"} and isinstance(value, str):
                values.append(value)
            elif isinstance(value, (dict, list)):
                values.extend(_payload_secrets(value))
    elif isinstance(payload, list):
        for item in payload:
            values.extend(_payload_secrets(item))
    return tuple(values)


def _request_json(
    credentials: ZendeskCredentials,
    method: str,
    path_or_url: str,
    payload: dict | None = None,
) -> dict:
    base = f"https://{credentials.subdomain}.zendesk.com"
    if path_or_url.startswith("http"):
        parsed = urlsplit(path_or_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname != f"{credentials.subdomain}.zendesk.com"
        ):
            raise ZendeskError("Zendesk returned an unexpected pagination URL.")
        url = path_or_url
    else:
        url = base + path_or_url

    try:
        response = httpx.request(
            method,
            url,
            json=payload,
            auth=(f"{credentials.email}/token", credentials.token),
            timeout=15.0,
            headers={
                "Accept": "application/json",
                "User-Agent": "RoyalTyresAssetPortal/0.3",
            },
        )
    except httpx.HTTPError as exc:
        raise ZendeskError("Zendesk could not be reached. Try the connection again.") from exc

    safe_path = urlsplit(url).path
    if response.status_code in {401, 403}:
        raise ZendeskError(
            "Zendesk rejected the configured credentials or the user lacks permission for this action.",
            400,
        )
    if response.status_code >= 400:
        basic_value = base64.b64encode(
            f"{credentials.email}/token:{credentials.token}".encode()
        ).decode()
        detail = _safe_zendesk_error(
            response, (credentials.token, basic_value, *_payload_secrets(payload))
        )
        logger.warning(
            "Zendesk API failure method=%s path=%s status=%s detail=%s",
            method,
            safe_path,
            response.status_code,
            detail or "none",
        )
        suffix = f": {detail}" if detail else "."
        raise ZendeskError(
            f"Zendesk returned HTTP {response.status_code} for {method} {safe_path}{suffix}",
            502,
        )

    if response.status_code == 204 or not response.content:
        return {}
    try:
        data = response.json()
    except ValueError as exc:
        raise ZendeskError("Zendesk returned an invalid JSON response.") from exc
    return data if isinstance(data, dict) else {}


def _list_all(
    credentials: ZendeskCredentials, path: str, root_key: str
) -> list[dict]:
    separator = "&" if "?" in path else "?"
    next_url: str | None = f"{path}{separator}per_page=100"
    items: list[dict] = []
    pages = 0
    while next_url and pages < 20:
        data = _request_json(credentials, "GET", next_url)
        page_items = data.get(root_key, [])
        if isinstance(page_items, list):
            items.extend(item for item in page_items if isinstance(item, dict))
        next_url = data.get("next_page")
        pages += 1
    return items


def _list_webhooks(credentials: ZendeskCredentials) -> list[dict]:
    data = _request_json(credentials, "GET", "/api/v2/webhooks")
    webhooks = data.get("webhooks", [])
    return [item for item in webhooks if isinstance(item, dict)] if isinstance(webhooks, list) else []


def _find_named(items: list[dict], wanted: str) -> dict | None:
    key = wanted.casefold()
    for item in items:
        value = item.get("name") or item.get("title") or item.get("display_name")
        if isinstance(value, str) and value.casefold() == key:
            return item
    return None


def _discover(credentials: ZendeskCredentials) -> dict[str, list[dict]]:
    return {
        "brands": _list_all(credentials, "/api/v2/brands.json", "brands"),
        "groups": _list_all(credentials, "/api/v2/groups.json", "groups"),
        "fields": _list_all(credentials, "/api/v2/ticket_fields.json", "ticket_fields"),
        "forms": _list_all(credentials, "/api/v2/ticket_forms.json", "ticket_forms"),
        "views": _list_all(credentials, "/api/v2/views.json", "views"),
        "targets": _list_all(credentials, "/api/v2/targets", "targets"),
        "webhooks": _list_webhooks(credentials),
        "triggers": _list_all(credentials, "/api/v2/triggers.json", "triggers"),
    }


def _usable_id(value) -> int | str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return value
    return None


def _plan_item(
    key: str,
    object_type: str,
    name: str,
    match: dict | None,
    details: str | None = None,
) -> dict:
    object_id = _usable_id(match.get("id")) if match else None
    return {
        "key": key,
        "object_type": object_type,
        "name": name,
        "action": "reuse" if object_id is not None else "create",
        "existing_id": object_id,
        "details": details,
    }


def build_setup_plan(credentials: ZendeskCredentials, settings: Settings) -> list[dict]:
    current = _discover(credentials)
    plan = [
        _plan_item("brand", "Brand", BRAND_NAME, _find_named(current["brands"], BRAND_NAME)),
        _plan_item("group", "Group", GROUP_NAME, _find_named(current["groups"], GROUP_NAME)),
    ]
    for key, definition in FIELD_DEFINITIONS.items():
        plan.append(
            _plan_item(
                key,
                "Ticket field",
                definition["title"],
                _find_named(current["fields"], definition["title"]),
            )
        )
    plan.extend(
        [
            _plan_item("ticket_form", "Ticket form", FORM_NAME, _find_named(current["forms"], FORM_NAME)),
            _plan_item("view", "View", VIEW_NAME, _find_named(current["views"], VIEW_NAME)),
            _plan_item(
                "email_target",
                "Email target",
                EMAIL_TARGET_NAME,
                _find_named(current["targets"], EMAIL_TARGET_NAME),
                f"Receiver: {settings.zendesk_notification_email.strip()}",
            ),
            _plan_item(
                "status_webhook",
                "Webhook",
                WEBHOOK_NAME,
                _find_named(current["webhooks"], WEBHOOK_NAME),
                "POST status changes back to the hosted FastAPI portal using bearer authentication.",
            ),
            _plan_item(
                "trigger_new_email",
                "Trigger",
                TRIGGER_NEW_EMAIL_NAME,
                _find_named(current["triggers"], TRIGGER_NEW_EMAIL_NAME),
                "Active after approved apply; emails the demo receiver when a portal ticket is created.",
            ),
            _plan_item(
                "trigger_status_email",
                "Trigger",
                TRIGGER_STATUS_EMAIL_NAME,
                _find_named(current["triggers"], TRIGGER_STATUS_EMAIL_NAME),
                "Active after approved apply; emails the demo receiver when ticket status changes.",
            ),
            _plan_item(
                "trigger_status_sync",
                "Trigger",
                TRIGGER_STATUS_SYNC_NAME,
                _find_named(current["triggers"], TRIGGER_STATUS_SYNC_NAME),
                "Active after approved apply; updates Track a request through the authenticated webhook.",
            ),
        ]
    )
    return plan


def get_connection(db: Session) -> ZendeskConnection | None:
    return db.get(ZendeskConnection, 1)


def _ids(connection: ZendeskConnection) -> dict[str, int | None]:
    return {field: getattr(connection, field) for field in ID_FIELDS}


def is_configured(db: Session) -> bool:
    connection = get_connection(db)
    return bool(connection and all(getattr(connection, field) for field in ID_FIELDS))


def is_configured_record(connection: ZendeskConnection) -> bool:
    return bool(all(getattr(connection, field) for field in ID_FIELDS))


def _workflow_environment_ready(settings: Settings) -> bool:
    secret = settings.zendesk_webhook_secret.get_secret_value().strip()
    email = settings.zendesk_notification_email.strip()
    url = settings.render_external_url.strip()
    if not secret or not email or not url:
        return False
    parsed = urlsplit(url)
    return parsed.scheme == "https" and bool(parsed.hostname)


def _webhook_endpoint(settings: Settings) -> str:
    if not _workflow_environment_ready(settings):
        raise ZendeskError(
            "Zendesk workflow setup requires ZENDESK_WEBHOOK_SECRET and the Render HTTPS public URL. Set ZENDESK_WEBHOOK_SECRET in Render, then refresh the plan.",
            503,
        )
    return f"{settings.render_external_url.strip().rstrip('/')}/api/webhooks/zendesk"


def _status(
    connection: ZendeskConnection | None,
    settings: Settings,
    plan: list[dict] | None = None,
    verification: list[dict] | None = None,
    message: str = "",
    environment_configured: bool = True,
) -> dict:
    workflow_ready = _workflow_environment_ready(settings)
    common = {
        "environment_configured": environment_configured,
        "workflow_environment_ready": workflow_ready,
        "notification_email": settings.zendesk_notification_email.strip() or None,
        "plan": plan or [],
        "verification": verification or [],
        "message": message,
    }
    if connection is None:
        return {
            **common,
            "connected": False,
            "configured": False,
            "can_configure": False,
            "instance": None,
            "user": None,
            "ids": None,
            "message": message or "Test the Zendesk environment connection to build the setup plan.",
        }
    return {
        **common,
        "connected": True,
        "configured": is_configured_record(connection),
        "can_configure": connection.connected_user_role == "admin" and workflow_ready,
        "instance": f"{connection.subdomain}.zendesk.com",
        "user": {
            "name": connection.connected_user_name,
            "email": connection.connected_user_email,
            "role": connection.connected_user_role,
        },
        "ids": _ids(connection),
    }


def _environment_ready(settings: Settings) -> bool:
    return bool(
        settings.zendesk_subdomain.strip()
        and settings.zendesk_email.strip()
        and settings.zendesk_api_token.get_secret_value().strip()
    )


def get_setup_status(db: Session, settings: Settings) -> dict:
    if not _environment_ready(settings):
        return _status(
            None,
            settings,
            environment_configured=False,
            message="Zendesk environment variables are not configured on the backend.",
        )

    connection = get_connection(db)
    if connection is None:
        return _status(
            None,
            settings,
            environment_configured=True,
            message="Zendesk credentials are present in the backend environment. Test the connection to build the dry-run plan.",
        )

    credentials = _credentials_from_settings(settings)
    if (
        connection.subdomain != credentials.subdomain
        or connection.api_email.casefold() != credentials.email.casefold()
    ):
        return _status(
            None,
            settings,
            environment_configured=True,
            message="Zendesk environment values changed. Test the connection again before applying configuration.",
        )

    plan = build_setup_plan(credentials, settings)
    if not _workflow_environment_ready(settings):
        message = "Connection verified. Add ZENDESK_WEBHOOK_SECRET in Render before applying the full notification and status-sync plan."
    else:
        message = (
            "Zendesk is configured and verified. You can rerun the full plan safely."
            if is_configured_record(connection)
            else "Connection verified. Review the complete dry-run plan before applying configuration."
        )
    return _status(connection, settings, plan, message=message)


def connect(db: Session, settings: Settings) -> dict:
    credentials = _credentials_from_settings(settings)
    data = _request_json(credentials, "GET", "/api/v2/users/me.json")
    user = data.get("user") if isinstance(data, dict) else None
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise ZendeskError("Zendesk login succeeded but returned an invalid user response.")

    connection = get_connection(db)
    changed_instance = bool(
        connection
        and (
            connection.subdomain != credentials.subdomain
            or connection.api_email.casefold() != credentials.email.casefold()
        )
    )
    if connection is None:
        connection = ZendeskConnection(id=1, subdomain=credentials.subdomain, api_email=credentials.email)
        db.add(connection)
    else:
        connection.subdomain = credentials.subdomain
        connection.api_email = credentials.email

    connection.connected_user_name = user.get("name")
    connection.connected_user_email = user.get("email")
    connection.connected_user_role = user.get("role")
    connection.connected_at = utc_now()

    if changed_instance:
        for field in ID_FIELDS:
            setattr(connection, field, None)
        connection.configured_at = None
        connection.verified_at = None

    db.commit()
    db.refresh(connection)

    plan = build_setup_plan(credentials, settings)
    if connection.connected_user_role != "admin":
        message = "Connection verified, but an admin user is required to create Zendesk configuration."
    elif not _workflow_environment_ready(settings):
        message = "Connection verified. Add ZENDESK_WEBHOOK_SECRET in Render before applying notifications and status sync."
    else:
        message = "Connection verified from backend environment variables. Review the complete plan and confirm before any Zendesk configuration is changed."
    return _status(connection, settings, plan, message=message)


def _ensure_brand(credentials: ZendeskCredentials) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/brands.json", "brands"), BRAND_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    subdomain = f"{credentials.subdomain}-royal-tyres"[:99].strip("-")
    data = _request_json(credentials, "POST", "/api/v2/brands.json", {"brand": {"name": BRAND_NAME, "subdomain": subdomain}})
    item = data.get("brand")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created brand ID.")
    return item["id"]


def _ensure_group(credentials: ZendeskCredentials) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/groups.json", "groups"), GROUP_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    data = _request_json(credentials, "POST", "/api/v2/groups.json", {"group": {"name": GROUP_NAME}})
    item = data.get("group")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created group ID.")
    return item["id"]


def _ensure_field(credentials: ZendeskCredentials, definition: dict) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/ticket_fields.json", "ticket_fields"), definition["title"])
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]

    field = {
        "title": definition["title"],
        "type": definition["type"],
        "active": True,
        "required": False,
        "required_in_portal": False,
        "visible_in_portal": False,
        "editable_in_portal": False,
    }
    if definition.get("custom_field_options"):
        field["custom_field_options"] = definition["custom_field_options"]
    data = _request_json(credentials, "POST", "/api/v2/ticket_fields.json", {"ticket_field": field})
    item = data.get("ticket_field")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError(f"Zendesk did not return the field ID for {definition['title']}.")
    return item["id"]


def _ensure_form(credentials: ZendeskCredentials, brand_id: int, field_ids: list[int]) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/ticket_forms.json", "ticket_forms"), FORM_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/ticket_forms.json",
        {
            "ticket_form": {
                "name": FORM_NAME,
                "display_name": "IT Asset Request",
                "active": True,
                "end_user_visible": False,
                "in_all_brands": False,
                "restricted_brand_ids": [brand_id],
                "ticket_field_ids": field_ids,
            }
        },
    )
    item = data.get("ticket_form")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created ticket form ID.")
    return item["id"]


def _ensure_view(credentials: ZendeskCredentials, group_id: int) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/views.json", "views"), VIEW_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/views.json",
        {
            "view": {
                "title": VIEW_NAME,
                "active": True,
                "all": [
                    {"field": "group_id", "operator": "is", "value": str(group_id)},
                    {"field": "current_tags", "operator": "includes", "value": PORTAL_TAG},
                ],
                "any": [],
                "output": {"columns": ["status", "requester", "description", "priority", "updated"]},
            }
        },
    )
    item = data.get("view")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created view ID.")
    return item["id"]


def _ensure_email_target(credentials: ZendeskCredentials, settings: Settings) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/targets", "targets"), EMAIL_TARGET_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    email = settings.zendesk_notification_email.strip()
    if not email:
        raise ZendeskError("ZENDESK_NOTIFICATION_EMAIL is empty.", 503)
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/targets",
        {
            "target": {
                "type": "email_target",
                "title": EMAIL_TARGET_NAME,
                "email": email,
                "subject": EMAIL_TARGET_SUBJECT,
                "active": True,
            }
        },
    )
    item = data.get("target")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created email target ID.")
    return item["id"]


def _ensure_webhook(credentials: ZendeskCredentials, settings: Settings) -> str:
    existing = _find_named(_list_webhooks(credentials), WEBHOOK_NAME)
    if existing and _usable_id(existing.get("id")) is not None:
        return str(existing["id"])

    secret = settings.zendesk_webhook_secret.get_secret_value().strip()
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/webhooks",
        {
            "webhook": {
                "name": WEBHOOK_NAME,
                "status": "active",
                "endpoint": _webhook_endpoint(settings),
                "http_method": "POST",
                "request_format": "json",
                "subscriptions": ["conditional_ticket_events"],
                "authentication": {
                    "type": "bearer_token",
                    "data": {"token": secret},
                    "add_position": "header",
                },
            }
        },
    )
    item = data.get("webhook")
    webhook_id = _usable_id(item.get("id")) if isinstance(item, dict) else None
    if webhook_id is None:
        raise ZendeskError("Zendesk did not return the created webhook ID.")
    return str(webhook_id)


def _trigger_definition(title: str, conditions: dict, actions: list[dict]) -> dict:
    return {
        "title": title,
        "active": True,
        "conditions": conditions,
        "actions": actions,
    }


def _ensure_trigger(credentials: ZendeskCredentials, definition: dict) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/triggers.json", "triggers"), definition["title"])
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]

    # Zendesk can validate trigger conditions/actions without creating anything.
    _request_json(credentials, "POST", "/api/v2/triggers/validate", {"trigger": definition})
    data = _request_json(credentials, "POST", "/api/v2/triggers", {"trigger": definition})
    item = data.get("trigger")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError(f"Zendesk did not return the trigger ID for {definition['title']}.")
    return item["id"]


def _new_request_email_trigger(target_id: int) -> dict:
    body = (
        "New Royal Tyres IT asset request\n\n"
        "Zendesk ticket: #{{ticket.id}}\n"
        "Subject: {{ticket.title}}\n"
        "Status: {{ticket.status}}\n\n"
        "This notification was generated by the Royal Tyres Asset Portal demo."
    )
    return _trigger_definition(
        TRIGGER_NEW_EMAIL_NAME,
        {
            "all": [
                {"field": "current_tags", "operator": "includes", "value": PORTAL_TAG},
                {"field": "update_type", "value": "Create"},
            ],
            "any": [],
        },
        [{"field": "notification_target", "value": [str(target_id), body]}],
    )


def _status_email_trigger(target_id: int) -> dict:
    body = (
        "Royal Tyres IT asset request status updated\n\n"
        "Zendesk ticket: #{{ticket.id}}\n"
        "Subject: {{ticket.title}}\n"
        "New status: {{ticket.status}}\n\n"
        "The hosted Track a request page is updated by the companion webhook."
    )
    return _trigger_definition(
        TRIGGER_STATUS_EMAIL_NAME,
        {
            "all": [
                {"field": "current_tags", "operator": "includes", "value": PORTAL_TAG},
                {"field": "update_type", "value": "Change"},
                {"field": "status", "operator": "changed"},
            ],
            "any": [],
        },
        [{"field": "notification_target", "value": [str(target_id), body]}],
    )


def _status_sync_trigger(webhook_id: str) -> dict:
    webhook_body = json.dumps(
        {
            "event": "status_changed",
            "ticket_id": "{{ticket.id}}",
            "external_id": "{{ticket.external_id}}",
            "status": "{{ticket.status}}",
        },
        separators=(",", ":"),
    )
    return _trigger_definition(
        TRIGGER_STATUS_SYNC_NAME,
        {
            "all": [
                {"field": "current_tags", "operator": "includes", "value": PORTAL_TAG},
                {"field": "update_type", "value": "Change"},
                {"field": "status", "operator": "changed"},
            ],
            "any": [],
        },
        [{"field": "notification_webhook", "value": [webhook_id, webhook_body]}],
    )


def _verify_object(
    credentials: ZendeskCredentials,
    object_type: str,
    object_id: int | str,
    path: str,
    root_key: str,
) -> dict:
    data = _request_json(credentials, "GET", path)
    item = data.get(root_key)
    ok = isinstance(item, dict) and str(item.get("id")) == str(object_id)
    return {
        "object_type": object_type,
        "id": object_id,
        "ok": ok,
        "result": "PASS" if ok else "FAIL",
    }


def apply_setup(db: Session, settings: Settings) -> dict:
    connection = get_connection(db)
    if connection is None:
        raise ZendeskError("Test the Zendesk environment connection before applying configuration.", 400)
    if connection.connected_user_role != "admin":
        raise ZendeskError("A Zendesk admin user is required to apply configuration.", 403)
    if not _workflow_environment_ready(settings):
        raise ZendeskError(
            "Add ZENDESK_WEBHOOK_SECRET in Render before applying the complete notification and status-sync configuration.",
            503,
        )

    credentials = _credentials_from_settings(settings)
    if (
        connection.subdomain != credentials.subdomain
        or connection.api_email.casefold() != credentials.email.casefold()
    ):
        raise ZendeskError("Zendesk environment values changed. Test the connection again before applying configuration.", 409)

    # Dependency order mirrors the proven setup approach: data model first,
    # then UI resources, then notification target/webhook, then active triggers.
    # Every ensure re-reads Zendesk so partial prior runs are safely reusable.
    brand_id = _ensure_brand(credentials)
    group_id = _ensure_group(credentials)
    asset_type_field_id = _ensure_field(credentials, FIELD_DEFINITIONS["asset_type_field"])
    local_request_id_field_id = _ensure_field(credentials, FIELD_DEFINITIONS["local_request_id_field"])
    request_source_field_id = _ensure_field(credentials, FIELD_DEFINITIONS["request_source_field"])
    ticket_form_id = _ensure_form(
        credentials,
        brand_id,
        [asset_type_field_id, local_request_id_field_id, request_source_field_id],
    )
    view_id = _ensure_view(credentials, group_id)
    email_target_id = _ensure_email_target(credentials, settings)
    webhook_id = _ensure_webhook(credentials, settings)
    new_email_trigger_id = _ensure_trigger(credentials, _new_request_email_trigger(email_target_id))
    status_email_trigger_id = _ensure_trigger(credentials, _status_email_trigger(email_target_id))
    status_sync_trigger_id = _ensure_trigger(credentials, _status_sync_trigger(webhook_id))

    verification = [
        _verify_object(credentials, "Brand", brand_id, f"/api/v2/brands/{brand_id}.json", "brand"),
        _verify_object(credentials, "Group", group_id, f"/api/v2/groups/{group_id}.json", "group"),
        _verify_object(credentials, "Asset Type field", asset_type_field_id, f"/api/v2/ticket_fields/{asset_type_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Local Request ID field", local_request_id_field_id, f"/api/v2/ticket_fields/{local_request_id_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Request Source field", request_source_field_id, f"/api/v2/ticket_fields/{request_source_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Ticket form", ticket_form_id, f"/api/v2/ticket_forms/{ticket_form_id}.json", "ticket_form"),
        _verify_object(credentials, "View", view_id, f"/api/v2/views/{view_id}.json", "view"),
        _verify_object(credentials, "Email target", email_target_id, f"/api/v2/targets/{email_target_id}", "target"),
        _verify_object(credentials, "Webhook", webhook_id, f"/api/v2/webhooks/{webhook_id}", "webhook"),
        _verify_object(credentials, "New request email trigger", new_email_trigger_id, f"/api/v2/triggers/{new_email_trigger_id}.json", "trigger"),
        _verify_object(credentials, "Status email trigger", status_email_trigger_id, f"/api/v2/triggers/{status_email_trigger_id}.json", "trigger"),
        _verify_object(credentials, "Status sync trigger", status_sync_trigger_id, f"/api/v2/triggers/{status_sync_trigger_id}.json", "trigger"),
    ]
    if not all(item["ok"] for item in verification):
        db.rollback()
        raise ZendeskError("Zendesk configuration was applied but post-change verification failed.")

    connection.brand_id = brand_id
    connection.group_id = group_id
    connection.asset_type_field_id = asset_type_field_id
    connection.local_request_id_field_id = local_request_id_field_id
    connection.request_source_field_id = request_source_field_id
    connection.ticket_form_id = ticket_form_id
    connection.view_id = view_id
    connection.configured_at = utc_now()
    connection.verified_at = utc_now()
    db.commit()
    db.refresh(connection)

    plan = build_setup_plan(credentials, settings)
    return _status(
        connection,
        settings,
        plan,
        verification,
        "Zendesk configuration, demo email notifications and Track a request status sync were applied and verified successfully.",
    )


def _asset_value(asset_type: str) -> str:
    return asset_type.strip().lower().replace(" ", "_")


def create_ticket(settings: Settings, db: Session, record: AssetRequest) -> dict:
    """Create one Zendesk ticket using Render-held credentials and verified IDs."""
    connection = get_connection(db)
    if connection is None or not is_configured_record(connection):
        raise ZendeskError("Zendesk integration is not configured.", 503)

    credentials = _credentials_from_settings(settings)
    if (
        connection.subdomain != credentials.subdomain
        or connection.api_email.casefold() != credentials.email.casefold()
    ):
        raise ZendeskError("Zendesk environment values changed. Re-test the connection.", 503)

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
            "requester": {"name": record.requester_name, "email": record.requester_email},
            "external_id": f"royal-tires-asset-{record.id}",
            "brand_id": connection.brand_id,
            "group_id": connection.group_id,
            "ticket_form_id": connection.ticket_form_id,
            "custom_fields": [
                {"id": connection.asset_type_field_id, "value": _asset_value(record.asset_type)},
                {"id": connection.local_request_id_field_id, "value": str(record.id)},
                {"id": connection.request_source_field_id, "value": PORTAL_TAG},
            ],
            "tags": ["it_asset_request", PORTAL_TAG, f"local_request_{record.id}"],
            "priority": "normal",
        }
    }

    data = _request_json(credentials, "POST", "/api/v2/tickets.json", payload)
    ticket = data.get("ticket") if isinstance(data, dict) else None
    if not isinstance(ticket, dict) or not isinstance(ticket.get("id"), int):
        raise ZendeskError("Zendesk returned an invalid ticket response.")
    return ticket
