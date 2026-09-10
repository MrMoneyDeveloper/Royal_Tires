"""
ROLE: Opt-in Service for seven confirmed legacy trigger exclusions
CALLED BY: Zendesk Controller within governed setup
CALLS: ZendeskService HTTP/discovery helpers
DATA IN: Settings and discovered Royal Tyres brand ID
DATA OUT: UPDATE/REUSE/SKIP plan and preservation verification
WHY: Isolate known sandbox interference without disabling unrelated automation.
SECURITY / RELIABILITY: Only listed titles may change. Adds Brand IS NOT Royal Tyres and
    resends existing actions because updating conditions alone can clear actions. Snapshots
    contribute to the controller plan; read-back compares protected properties.
FLOW: Zendesk Controller within governed setup -> this module -> ZendeskService HTTP/discovery
    helpers
"""

import hashlib
import json
from copy import deepcopy

from app.core.config import Settings
from app.services import zendesk_service

LEGACY_TRIGGER_TITLES = (
    "Issue Category 1",
    "Request Type 4",
    "Query Type 6",
    "Issue Type 6",
    "Request Type 6",
    "Query Type 5",
    "hello world",
)


def _brand_exclusion(brand_id: int) -> dict:
    return {"field": "brand_id", "operator": "is_not", "value": str(brand_id)}


def _trigger_snapshot(trigger: dict) -> str:
    """Fingerprint only the trigger properties that must remain unchanged."""
    protected = {
        key: trigger.get(key)
        for key in (
            "id",
            "title",
            "active",
            "description",
            "category_id",
            "position",
            "conditions",
            "actions",
        )
    }
    canonical = json.dumps(protected, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _matching_trigger(triggers: list[dict], title: str) -> dict | None:
    matches = [
        trigger
        for trigger in triggers
        if isinstance(trigger.get("title"), str)
        and trigger["title"].casefold() == title.casefold()
    ]
    if len(matches) > 1:
        raise zendesk_service.ZendeskError(
            f"Multiple Zendesk triggers match '{title}'. Resolve the duplicate before applying the Royal Tyres safeguard.",
            409,
        )
    return matches[0] if matches else None


def _has_exclusion(trigger: dict, brand_id: int | None) -> bool:
    if not brand_id:
        return False
    conditions = trigger.get("conditions")
    all_conditions = conditions.get("all", []) if isinstance(conditions, dict) else []
    expected = _brand_exclusion(brand_id)
    return any(
        isinstance(condition, dict)
        and condition.get("field") == expected["field"]
        and condition.get("operator") == expected["operator"]
        and str(condition.get("value")) == expected["value"]
        for condition in all_conditions
    )


def build_plan(settings: Settings) -> list[dict]:
    """Describe the seven narrow sandbox safeguards without mutating Zendesk."""
    credentials = zendesk_service._credentials_from_settings(settings)
    brands = zendesk_service._list_all(credentials, "/api/v2/brands.json", "brands")
    triggers = zendesk_service._list_all(credentials, "/api/v2/triggers.json", "triggers")
    brand = zendesk_service._find_named(brands, zendesk_service.BRAND_NAME)
    brand_id = brand.get("id") if isinstance(brand, dict) and isinstance(brand.get("id"), int) else None

    plan = []
    for index, title in enumerate(LEGACY_TRIGGER_TITLES, start=1):
        trigger = _matching_trigger(triggers, title)
        if trigger is None:
            plan.append(
                {
                    "key": f"legacy_trigger_guard_{index}",
                    "object_type": "Existing trigger safeguard",
                    "name": title,
                    "action": "skip",
                    "existing_id": None,
                    "details": "Trigger is not present in this Zendesk instance; no change is required.",
                }
            )
            continue

        trigger_id = trigger.get("id") if isinstance(trigger.get("id"), int) else None
        snapshot = _trigger_snapshot(trigger)[:12]
        protected = _has_exclusion(trigger, brand_id)
        plan.append(
            {
                "key": f"legacy_trigger_guard_{index}",
                "object_type": "Existing trigger safeguard",
                "name": title,
                "action": "reuse" if protected else "update",
                "existing_id": trigger_id,
                "details": (
                    f"Already excludes {zendesk_service.BRAND_NAME}; config ref {snapshot}."
                    if protected
                    else f"Add Brand IS NOT {zendesk_service.BRAND_NAME}; preserve every other condition/action/state; config ref {snapshot}."
                ),
            }
        )
    return plan


def _update_payload(original: dict, brand_id: int) -> dict:
    conditions = deepcopy(original.get("conditions") or {})
    all_conditions = list(conditions.get("all") or [])
    any_conditions = list(conditions.get("any") or [])
    all_conditions.append(_brand_exclusion(brand_id))

    trigger = {
        "conditions": {"all": all_conditions, "any": any_conditions},
        # Zendesk clears both conditions and actions when either is updated, so
        # the existing actions must be sent back intact with the new condition.
        "actions": deepcopy(original.get("actions") or []),
    }
    for key in ("title", "active", "description", "category_id"):
        if key in original:
            trigger[key] = deepcopy(original[key])
    return {"trigger": trigger}


def _unchanged_except_exclusion(original: dict, updated: dict, brand_id: int) -> bool:
    if not _has_exclusion(updated, brand_id):
        return False

    for key in ("title", "active", "description", "category_id", "position", "actions"):
        if original.get(key) != updated.get(key):
            return False

    original_conditions = original.get("conditions") or {}
    updated_conditions = updated.get("conditions") or {}
    expected_all = list(original_conditions.get("all") or []) + [_brand_exclusion(brand_id)]
    return (
        updated_conditions.get("all", []) == expected_all
        and updated_conditions.get("any", []) == original_conditions.get("any", [])
    )


def apply_exclusions(settings: Settings, brand_id: int) -> list[dict]:
    """Add one brand exclusion to each confirmed legacy trigger and verify it."""
    credentials = zendesk_service._credentials_from_settings(settings)
    summaries = zendesk_service._list_all(credentials, "/api/v2/triggers.json", "triggers")
    verification = []

    for title in LEGACY_TRIGGER_TITLES:
        summary = _matching_trigger(summaries, title)
        if summary is None:
            verification.append(
                {
                    "object_type": f"Legacy trigger safeguard: {title}",
                    "id": None,
                    "ok": True,
                    "result": "SKIP",
                }
            )
            continue

        trigger_id = summary.get("id")
        if not isinstance(trigger_id, int):
            raise zendesk_service.ZendeskError(
                f"Zendesk trigger '{title}' did not provide a numeric ID.", 502
            )

        live = zendesk_service._request_json(
            credentials, "GET", f"/api/v2/triggers/{trigger_id}.json"
        ).get("trigger")
        if not isinstance(live, dict):
            raise zendesk_service.ZendeskError(
                f"Zendesk returned an invalid trigger response for '{title}'.", 502
            )
        if live.get("title", "").casefold() != title.casefold():
            raise zendesk_service.ZendeskError(
                f"Zendesk trigger '{title}' changed identity before update.", 409
            )

        if _has_exclusion(live, brand_id):
            verification.append(
                {
                    "object_type": f"Legacy trigger safeguard: {title}",
                    "id": trigger_id,
                    "ok": True,
                    "result": "PASS",
                }
            )
            continue

        original = deepcopy(live)
        payload = _update_payload(original, brand_id)
        zendesk_service._request_json(
            credentials, "POST", "/api/v2/triggers/validate", payload
        )
        zendesk_service._request_json(
            credentials, "PUT", f"/api/v2/triggers/{trigger_id}.json", payload
        )
        updated = zendesk_service._request_json(
            credentials, "GET", f"/api/v2/triggers/{trigger_id}.json"
        ).get("trigger")

        ok = isinstance(updated, dict) and _unchanged_except_exclusion(
            original, updated, brand_id
        )
        verification.append(
            {
                "object_type": f"Legacy trigger safeguard: {title}",
                "id": trigger_id,
                "ok": ok,
                "result": "PASS" if ok else "FAIL",
            }
        )
        if not ok:
            raise zendesk_service.ZendeskError(
                f"Zendesk trigger safeguard verification failed for '{title}'.",
                502,
            )

    return verification
