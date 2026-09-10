"""
ROLE: Pure integration identity helpers
CALLED BY: WebhookService and ZendeskService
CALLS: String formatting only
DATA IN: Local request ID or asset label
DATA OUT: Correlation external ID, request tag or namespaced asset value
WHY: Make deterministic identity rules understandable outside workflow code.
SECURITY / RELIABILITY: royal-tires-asset-{local_request_id} is correlation, not encryption,
    hashing or the database primary key. Outbound ticket creation and inbound correlation
    share the same deterministic identity rules.
FLOW: WebhookService and ZendeskService -> this module -> String formatting only
"""

def build_external_id(request_id: int) -> str:
    # ZendeskService sends this deterministic correlation ID; WebhookService rebuilds it, not an encrypted key.
    return f"royal-tires-asset-{request_id}"


def build_local_request_tag(request_id: int) -> str:
    return f"local_request_{request_id}"


def asset_type_to_zendesk_value(asset_type: str) -> str:
    # Return the namespaced dropdown value expected by zendesk_service.py's managed ticket fields.
    return "rt_asset_" + asset_type.strip().lower().replace(" ", "_")
