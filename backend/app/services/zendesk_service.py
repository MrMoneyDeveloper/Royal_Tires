import base64
import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database import utc_now
from app.models.asset_request import AssetRequest
from app.models.zendesk_connection import ZendeskConnection

_SUBDOMAIN = re.compile(r"^[a-z0-9][a-z0-9-]{0,98}[a-z0-9]$|^[a-z0-9]$")

BRAND_NAME = "Royal Tyres"
GROUP_NAME = "Royal Tyres | IT Service Desk"
FORM_NAME = "Royal Tyres | IT Asset Request"
VIEW_NAME = "Royal Tyres | IT Asset Requests"
PORTAL_TAG = "royal_tires_asset_portal"

FIELD_DEFINITIONS = {
    "asset_type_field": {
        "title": "RT | Asset Type",
        "type": "dropdown",
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
        "type": "dropdown",
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
            "Enter a valid Zendesk subdomain such as 'digify7' or 'digify7.zendesk.com'.",
            400,
        )
    return raw


def _fernet(settings: Settings) -> Fernet:
    secret = settings.config_encryption_key.get_secret_value()
    if len(secret) < 16:
        raise ZendeskError(
            "CONFIG_ENCRYPTION_KEY is not configured on the backend.",
            503,
        )
    derived = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def _encrypt_token(settings: Settings, token: str) -> str:
    return _fernet(settings).encrypt(token.encode("utf-8")).decode("ascii")


def _decrypt_token(settings: Settings, encrypted_token: str) -> str:
    try:
        return _fernet(settings).decrypt(encrypted_token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ZendeskError(
            "The stored Zendesk token can no longer be decrypted. Reconnect the Zendesk instance.",
            503,
        ) from exc


def _credentials_from_connection(
    connection: ZendeskConnection, settings: Settings
) -> ZendeskCredentials:
    return ZendeskCredentials(
        subdomain=connection.subdomain,
        email=connection.api_email,
        token=_decrypt_token(settings, connection.encrypted_api_token),
    )


def _request_json(
    credentials: ZendeskCredentials,
    method: str,
    path_or_url: str,
    payload: dict | None = None,
) -> dict:
    base = f"https://{credentials.subdomain}.zendesk.com"
    if path_or_url.startswith("http"):
        parsed = urlsplit(path_or_url)
        if parsed.scheme != "https" or parsed.hostname != f"{credentials.subdomain}.zendesk.com":
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
                "User-Agent": "RoyalTyresAssetPortal/0.2",
            },
        )
    except httpx.HTTPError as exc:
        raise ZendeskError("Zendesk could not be reached. Try the connection again.") from exc

    if response.status_code in {401, 403}:
        raise ZendeskError(
            "Zendesk rejected the credentials or the user lacks permission for this action.",
            400,
        )
    if response.status_code >= 400:
        raise ZendeskError(
            f"Zendesk returned HTTP {response.status_code} while processing the setup.",
            502,
        )

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
    }


def _plan_item(key: str, object_type: str, name: str, match: dict | None) -> dict:
    object_id = match.get("id") if match else None
    return {
        "key": key,
        "object_type": object_type,
        "name": name,
        "action": "reuse" if isinstance(object_id, int) else "create",
        "existing_id": object_id if isinstance(object_id, int) else None,
    }


def build_setup_plan(credentials: ZendeskCredentials) -> list[dict]:
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
        ]
    )
    return plan


def get_connection(db: Session) -> ZendeskConnection | None:
    return db.get(ZendeskConnection, 1)


def _ids(connection: ZendeskConnection) -> dict[str, int | None]:
    return {field: getattr(connection, field) for field in ID_FIELDS}


def is_configured(db: Session) -> bool:
    connection = get_connection(db)
    return bool(
        connection
        and connection.encrypted_api_token
        and all(getattr(connection, field) for field in ID_FIELDS[:-1])
    )


def _status(
    connection: ZendeskConnection | None,
    plan: list[dict] | None = None,
    verification: list[dict] | None = None,
    message: str = "",
) -> dict:
    if connection is None:
        return {
            "connected": False,
            "configured": False,
            "can_configure": False,
            "instance": None,
            "user": None,
            "plan": [],
            "ids": None,
            "verification": verification or [],
            "message": message or "Connect a Zendesk sandbox to build the setup plan.",
        }
    return {
        "connected": True,
        "configured": is_configured_record(connection),
        "can_configure": connection.connected_user_role == "admin",
        "instance": f"{connection.subdomain}.zendesk.com",
        "user": {
            "name": connection.connected_user_name,
            "email": connection.connected_user_email,
            "role": connection.connected_user_role,
        },
        "plan": plan or [],
        "ids": _ids(connection),
        "verification": verification or [],
        "message": message,
    }


def is_configured_record(connection: ZendeskConnection) -> bool:
    return bool(
        connection.encrypted_api_token
        and all(getattr(connection, field) for field in ID_FIELDS[:-1])
    )


def get_setup_status(db: Session, settings: Settings) -> dict:
    connection = get_connection(db)
    if connection is None:
        return _status(None)
    credentials = _credentials_from_connection(connection, settings)
    plan = build_setup_plan(credentials)
    return _status(
        connection,
        plan,
        message=(
            "Zendesk is configured and verified. You can rerun the plan safely."
            if is_configured_record(connection)
            else "Connection verified. Review the dry-run plan before applying configuration."
        ),
    )


def connect(
    db: Session,
    settings: Settings,
    subdomain: str,
    email: str,
    api_token: str,
) -> dict:
    normalized = normalize_subdomain(subdomain)
    credentials = ZendeskCredentials(normalized, email.strip(), api_token.strip())
    if not credentials.token:
        raise ZendeskError("Zendesk API token is required.", 400)

    # Validate the login before saving anything.
    data = _request_json(credentials, "GET", "/api/v2/users/me.json")
    user = data.get("user") if isinstance(data, dict) else None
    if not isinstance(user, dict) or not isinstance(user.get("id"), int):
        raise ZendeskError("Zendesk login succeeded but returned an invalid user response.")

    encrypted = _encrypt_token(settings, credentials.token)
    connection = get_connection(db)
    changed_instance = bool(
        connection
        and (
            connection.subdomain != normalized
            or connection.api_email.casefold() != credentials.email.casefold()
        )
    )
    if connection is None:
        connection = ZendeskConnection(id=1, subdomain=normalized, api_email=credentials.email, encrypted_api_token=encrypted)
        db.add(connection)
    else:
        connection.subdomain = normalized
        connection.api_email = credentials.email
        connection.encrypted_api_token = encrypted

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

    plan = build_setup_plan(credentials)
    return _status(
        connection,
        plan,
        message=(
            "Connection verified. Review the plan and confirm before any Zendesk configuration is changed."
            if connection.connected_user_role == "admin"
            else "Connection verified, but an admin user is required to create Zendesk configuration."
        ),
    )


def _ensure_brand(credentials: ZendeskCredentials) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/brands.json", "brands"), BRAND_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    subdomain = f"{credentials.subdomain}-royal-tyres"[:99].strip("-")
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/brands.json",
        {"brand": {"name": BRAND_NAME, "subdomain": subdomain}},
    )
    item = data.get("brand")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created brand ID.")
    return item["id"]


def _ensure_group(credentials: ZendeskCredentials) -> int:
    existing = _find_named(_list_all(credentials, "/api/v2/groups.json", "groups"), GROUP_NAME)
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/groups.json",
        {"group": {"name": GROUP_NAME}},
    )
    item = data.get("group")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created group ID.")
    return item["id"]


def _ensure_field(credentials: ZendeskCredentials, definition: dict) -> int:
    existing = _find_named(
        _list_all(credentials, "/api/v2/ticket_fields.json", "ticket_fields"),
        definition["title"],
    )
    if existing and isinstance(existing.get("id"), int):
        return existing["id"]

    field = {
        "title": definition["title"],
        "type": definition["type"],
        "active": True,
        "required": False,
        "visible_in_portal": False,
        "editable_in_portal": False,
    }
    if definition.get("custom_field_options"):
        field["custom_field_options"] = definition["custom_field_options"]
    data = _request_json(
        credentials,
        "POST",
        "/api/v2/ticket_fields.json",
        {"ticket_field": field},
    )
    item = data.get("ticket_field")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError(f"Zendesk did not return the field ID for {definition['title']}.")
    return item["id"]


def _ensure_form(
    credentials: ZendeskCredentials,
    brand_id: int,
    field_ids: list[int],
) -> int:
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
                "output": {
                    "columns": ["status", "requester", "subject", "priority", "updated"]
                },
            }
        },
    )
    item = data.get("view")
    if not isinstance(item, dict) or not isinstance(item.get("id"), int):
        raise ZendeskError("Zendesk did not return the created view ID.")
    return item["id"]


def _verify_object(
    credentials: ZendeskCredentials,
    object_type: str,
    object_id: int,
    path: str,
    root_key: str,
) -> dict:
    data = _request_json(credentials, "GET", path)
    item = data.get(root_key)
    ok = isinstance(item, dict) and item.get("id") == object_id
    return {
        "object_type": object_type,
        "id": object_id,
        "ok": ok,
        "result": "PASS" if ok else "FAIL",
    }


def apply_setup(db: Session, settings: Settings) -> dict:
    connection = get_connection(db)
    if connection is None:
        raise ZendeskError("Connect and test Zendesk before applying configuration.", 400)
    if connection.connected_user_role != "admin":
        raise ZendeskError("A Zendesk admin user is required to apply configuration.", 403)

    credentials = _credentials_from_connection(connection, settings)

    # Fresh discovery occurs before mutation. Every ensure function is idempotent:
    # it reuses an exact Royal Tyres object if one already exists and creates only
    # the missing object. Unrelated Zendesk configuration is never deleted.
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

    connection.brand_id = brand_id
    connection.group_id = group_id
    connection.asset_type_field_id = asset_type_field_id
    connection.local_request_id_field_id = local_request_id_field_id
    connection.request_source_field_id = request_source_field_id
    connection.ticket_form_id = ticket_form_id
    connection.view_id = view_id
    connection.configured_at = utc_now()

    verification = [
        _verify_object(credentials, "Brand", brand_id, f"/api/v2/brands/{brand_id}.json", "brand"),
        _verify_object(credentials, "Group", group_id, f"/api/v2/groups/{group_id}.json", "group"),
        _verify_object(credentials, "Asset Type field", asset_type_field_id, f"/api/v2/ticket_fields/{asset_type_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Local Request ID field", local_request_id_field_id, f"/api/v2/ticket_fields/{local_request_id_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Request Source field", request_source_field_id, f"/api/v2/ticket_fields/{request_source_field_id}.json", "ticket_field"),
        _verify_object(credentials, "Ticket form", ticket_form_id, f"/api/v2/ticket_forms/{ticket_form_id}.json", "ticket_form"),
        _verify_object(credentials, "View", view_id, f"/api/v2/views/{view_id}.json", "view"),
    ]
    if not all(item["ok"] for item in verification):
        db.commit()
        raise ZendeskError("Zendesk configuration was applied but post-change verification failed.")

    connection.verified_at = utc_now()
    db.commit()
    db.refresh(connection)
    plan = build_setup_plan(credentials)
    return _status(
        connection,
        plan,
        verification,
        "Zendesk configuration applied and verified successfully.",
    )


def _asset_value(asset_type: str) -> str:
    return asset_type.strip().lower().replace(" ", "_")


def create_ticket(settings: Settings, db: Session, record: AssetRequest) -> dict:
    """Create one Zendesk ticket using the verified configuration stored in SQL."""
    connection = get_connection(db)
    if connection is None or not is_configured_record(connection):
        raise ZendeskError("Zendesk integration is not configured.", 503)
    credentials = _credentials_from_connection(connection, settings)

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
            "brand_id": connection.brand_id,
            "group_id": connection.group_id,
            "ticket_form_id": connection.ticket_form_id,
            "custom_fields": [
                {"id": connection.asset_type_field_id, "value": _asset_value(record.asset_type)},
                {"id": connection.local_request_id_field_id, "value": str(record.id)},
                {"id": connection.request_source_field_id, "value": PORTAL_TAG},
            ],
            "tags": [
                "it_asset_request",
                PORTAL_TAG,
                f"local_request_{record.id}",
            ],
            "priority": "normal",
        }
    }

    data = _request_json(credentials, "POST", "/api/v2/tickets.json", payload)
    ticket = data.get("ticket") if isinstance(data, dict) else None
    if not isinstance(ticket, dict) or not isinstance(ticket.get("id"), int):
        raise ZendeskError("Zendesk returned an invalid ticket response.")
    return ticket
