import pytest

from app.core.config import Settings
from app.services import legacy_trigger_guard, zendesk_service


@pytest.fixture
def settings(tmp_path):
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'guard.db').as_posix()}",
        app_username="test-user",
        app_password="test-password",
        frontend_url="https://portal.example.com",
        zendesk_subdomain="example",
        zendesk_email="admin@example.com",
        zendesk_api_token="test-token",
        zendesk_webhook_secret="test-webhook-secret",
        zendesk_notification_email="notify@example.com",
        render_external_url="https://api.example.com",
        zendesk_legacy_trigger_guard_enabled=True,
    )


def _trigger(trigger_id, title, all_conditions=None):
    return {
        "id": trigger_id,
        "title": title,
        "active": True,
        "description": "legacy sandbox rule",
        "category_id": "123",
        "position": trigger_id,
        "conditions": {
            "all": list(all_conditions or [{"field": "status", "operator": "is", "value": "new"}]),
            "any": [{"field": "priority", "operator": "is", "value": "normal"}],
        },
        "actions": [{"field": "group_id", "value": "999"}],
    }


def test_plan_marks_update_reuse_and_missing(monkeypatch, settings):
    brand_id = 42
    needs_update = _trigger(101, legacy_trigger_guard.LEGACY_TRIGGER_TITLES[0])
    already_safe = _trigger(
        102,
        legacy_trigger_guard.LEGACY_TRIGGER_TITLES[1],
        [
            {"field": "status", "operator": "is", "value": "new"},
            {"field": "brand_id", "operator": "is_not", "value": str(brand_id)},
        ],
    )

    def fake_list(credentials, path, root_key):
        if root_key == "brands":
            return [{"id": brand_id, "name": zendesk_service.BRAND_NAME}]
        if root_key == "triggers":
            return [needs_update, already_safe]
        raise AssertionError(root_key)

    monkeypatch.setattr(zendesk_service, "_list_all", fake_list)
    plan = legacy_trigger_guard.build_plan(settings)

    assert plan[0]["action"] == "update"
    assert "Brand IS NOT Royal Tyres" in plan[0]["details"]
    assert "config ref" in plan[0]["details"]
    assert plan[1]["action"] == "reuse"
    assert all(item["action"] == "skip" for item in plan[2:])


def test_apply_adds_only_brand_exclusion_and_preserves_trigger(monkeypatch, settings):
    title = legacy_trigger_guard.LEGACY_TRIGGER_TITLES[0]
    original = _trigger(101, title)
    stored = {"trigger": original}
    calls = []

    monkeypatch.setattr(
        zendesk_service,
        "_list_all",
        lambda credentials, path, root_key: [original] if root_key == "triggers" else [],
    )

    def fake_request(credentials, method, path, payload=None):
        calls.append((method, path))
        if method == "GET":
            return {"trigger": stored["trigger"]}
        if path == "/api/v2/triggers/validate":
            assert payload["trigger"]["actions"] == original["actions"]
            return {}
        if method == "PUT":
            updated = dict(original)
            updated["conditions"] = payload["trigger"]["conditions"]
            stored["trigger"] = updated
            return {"trigger": updated}
        raise AssertionError((method, path))

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    results = legacy_trigger_guard.apply_exclusions(settings, 42)

    first = results[0]
    assert first["ok"] is True
    assert first["result"] == "PASS"
    exclusion = {"field": "brand_id", "operator": "is_not", "value": "42"}
    assert stored["trigger"]["conditions"]["all"] == original["conditions"]["all"] + [exclusion]
    assert stored["trigger"]["conditions"]["any"] == original["conditions"]["any"]
    assert stored["trigger"]["actions"] == original["actions"]
    assert stored["trigger"]["title"] == original["title"]
    assert stored["trigger"]["active"] == original["active"]
    assert stored["trigger"]["position"] == original["position"]
    assert ("POST", "/api/v2/triggers/validate") in calls
    assert ("PUT", "/api/v2/triggers/101.json") in calls
    assert len(results) == len(legacy_trigger_guard.LEGACY_TRIGGER_TITLES)
    assert all(item["ok"] for item in results)


def test_apply_is_idempotent_when_exclusion_already_exists(monkeypatch, settings):
    title = legacy_trigger_guard.LEGACY_TRIGGER_TITLES[0]
    trigger = _trigger(
        101,
        title,
        [
            {"field": "status", "operator": "is", "value": "new"},
            {"field": "brand_id", "operator": "is_not", "value": "42"},
        ],
    )
    monkeypatch.setattr(
        zendesk_service,
        "_list_all",
        lambda credentials, path, root_key: [trigger] if root_key == "triggers" else [],
    )

    writes = []

    def fake_request(credentials, method, path, payload=None):
        if method != "GET":
            writes.append((method, path))
        return {"trigger": trigger}

    monkeypatch.setattr(zendesk_service, "_request_json", fake_request)
    results = legacy_trigger_guard.apply_exclusions(settings, 42)

    assert results[0]["result"] == "PASS"
    assert writes == []


def test_duplicate_legacy_trigger_titles_stop_before_mutation(monkeypatch, settings):
    title = legacy_trigger_guard.LEGACY_TRIGGER_TITLES[0]
    duplicate_a = _trigger(101, title)
    duplicate_b = _trigger(102, title)

    monkeypatch.setattr(
        zendesk_service,
        "_list_all",
        lambda credentials, path, root_key: [duplicate_a, duplicate_b] if root_key == "triggers" else [{"id": 42, "name": zendesk_service.BRAND_NAME}],
    )

    with pytest.raises(zendesk_service.ZendeskError) as exc:
        legacy_trigger_guard.build_plan(settings)
    assert exc.value.status_code == 409
