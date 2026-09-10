def build_external_id(request_id: int) -> str:
    return f"royal-tires-asset-{request_id}"


def build_local_request_tag(request_id: int) -> str:
    return f"local_request_{request_id}"


def asset_type_to_zendesk_value(asset_type: str) -> str:
    return "rt_asset_" + asset_type.strip().lower().replace(" ", "_")
