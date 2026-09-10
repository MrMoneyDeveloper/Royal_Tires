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


def test_confirmed_hello_world_title_is_planned_without_matching_similar_rule(monkeypatch, settings):
    confirmed = _trigger(28978973387036, "hello world")
    similar = _trigger(999, "hello world?")
    monkeypatch.setattr(
        zendesk_service,
        "_list_all",
        lambda credentials, path, root_key: [confirmed, similar]
        if root_key == "triggers" else [{"id": 42, "name": "Royal Tyres"}],
    )
    plan = legacy_trigger_guard.build_plan(settings)
    matches = [item for item in plan if item["action"] == "update"]
    assert len(matches) == 1
    assert matches[0]["name"] == "hello world"
    assert matches[0]["existing_id"] == confirmed["id"]


@pytest.mark.parametrize("title,trigger_id", [
    ("Issue Category 2 2", 27601293620508),
    ("Request Type 5", 27625845148444),
    ("Query Type 7", 27650068343452),
    ("Issue Type 7", 27695967421724),
    ("Request Type 7", 27698487674012),
    ("Query Type 6 (2)", 28370722368028),
    ("Query Type 8", 27650061836572),
    ("Issue Type 8", 27695960731292),
    ("Request Type 8", 27698470929052),
    ("Query Type 7 (2)", 28370770616604),
    ("Query Type 9", 27650056621980),
    ("Query Type 10", 27650047286556),
    ("Issue Type 9", 27695960756636),
    ("Issue Type 10", 27695935951644),
    ("Request Type 9", 27698464442908),
    ("Request Type 10", 27698464469660),
    ("Request Type 11", 27698464480668),
    ("Request Type 6 (2)", 27698493243036),
    ("Request Type 7 (2)", 27698468769436),
    ("Request Type 8 (2)", 27698482470044),
    ("Request Type 9 (2)", 27698501217564),
    ("Request Type 10 (2)", 27698476163868),
    ("Request Type 11 (2)", 27698504442140),

])
def test_additional_approved_titles_do_not_match_similar_rules(monkeypatch, settings, title, trigger_id):
    confirmed = _trigger(trigger_id, title)
    similar = _trigger(999, title + " unrelated")
    monkeypatch.setattr(zendesk_service, "_list_all", lambda credentials, path, root_key:
        [confirmed, similar] if root_key == "triggers" else [{"id": 42, "name": "Royal Tyres"}])
    updates = [item for item in legacy_trigger_guard.build_plan(settings) if item["action"] == "update"]
    assert [(item["name"], item["existing_id"]) for item in updates] == [(title, trigger_id)]


def test_drift_between_discovery_and_mutation_stops_without_writes(monkeypatch, settings):
    original = _trigger(101, legacy_trigger_guard.LEGACY_TRIGGER_TITLES[0])
    changed = dict(original, actions=[{"field": "set_tags", "value": "changed"}])
    monkeypatch.setattr(zendesk_service, "_list_all", lambda *args: [original])
    writes = []
    def request(credentials, method, path, payload=None):
        if method != "GET":
            writes.append(method)
        return {"trigger": changed}
    monkeypatch.setattr(zendesk_service, "_request_json", request)
    with pytest.raises(zendesk_service.ZendeskError) as exc:
        legacy_trigger_guard.apply_exclusions(settings, 42)
    assert exc.value.status_code == 409
    assert writes == []
