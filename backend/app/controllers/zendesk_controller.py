"""
ROLE: Zendesk setup Controller and approval boundary
CALLED BY: Settings / ZendeskSetupView through api.js
CALLS: ZendeskService and optional legacy_trigger_guard
DATA IN: Authenticated connect/setup calls or explicit confirmation plus SHA-256 fingerprint
DATA OUT: Safe setup plan, verification results or HTTP errors
WHY: Translate integration errors and bind approval to a freshly discovered plan.
SECURITY / RELIABILITY: Rejects changed plans with 409. Connect reads Zendesk but saves local
    connection metadata. Managed plan fingerprints describe identity/actions; they are not
    full remote-object hashes.
FLOW: Settings / ZendeskSetupView through api.js -> this module -> ZendeskService and optional
    legacy_trigger_guard
"""

import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.data.session import get_db
from app.schemas.zendesk_schema import ZendeskApplyRequest, ZendeskSetupStatus
from app.services import legacy_trigger_guard, zendesk_service

router = APIRouter(
    prefix="/api/zendesk",
    tags=["Zendesk"],
    dependencies=[Depends(require_user)],
)

Database = Annotated[Session, Depends(get_db)]


def _translate(error: zendesk_service.ZendeskError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=str(error))


def _plan_fingerprint(plan: list[dict]) -> str:
    """Bind approval to the exact read-only plan the admin reviewed."""
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _with_legacy_guard_plan(status: dict, settings) -> dict:
    """Add the opt-in sandbox isolation changes to the same approval plan."""
    if not settings.zendesk_legacy_trigger_guard_enabled or not status.get("connected"):
        return status
    status = dict(status)
    status["plan"] = [
        *(status.get("plan") or []),
        *legacy_trigger_guard.build_plan(settings),
    ]
    return status


def _with_plan_fingerprint(status: dict) -> dict:
    status = dict(status)
    status["plan_fingerprint"] = _plan_fingerprint(status.get("plan") or [])
    return status


@router.get("/setup", response_model=ZendeskSetupStatus)
def get_setup(db: Database, request: Request):
    try:
        settings = request.app.state.settings
        # services/zendesk_service.py discovers remote state and returns a dry-run, without applying changes.
        status = zendesk_service.get_setup_status(db, settings)
        status = _with_legacy_guard_plan(status, settings)
        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error


@router.post("/connect", response_model=ZendeskSetupStatus)
def connect(db: Database, request: Request):
    """Test Zendesk credentials already configured in the backend environment."""
    try:
        settings = request.app.state.settings
        # zendesk_service.py tests server-held credentials and saves safe local metadata; remote setup stays unchanged.
        status = zendesk_service.connect(db, settings)
        status = _with_legacy_guard_plan(status, settings)
        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error


# schemas/zendesk_schema.py validates confirmation/fingerprint shape; this Controller enforces reviewed-plan equality.
@router.post("/apply", response_model=ZendeskSetupStatus)
def apply_setup(data: ZendeskApplyRequest, db: Database, request: Request):
    if data.confirm is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit confirmation is required before Zendesk configuration is changed.",
        )
    try:
        settings = request.app.state.settings
        # Re-read Zendesk immediately before mutation and refuse to deploy if the
        # current plan no longer matches the exact preview the admin approved.
        current = zendesk_service.get_setup_status(db, settings)
        current = _with_legacy_guard_plan(current, settings)
        current_fingerprint = _plan_fingerprint(current.get("plan") or [])
        if data.plan_fingerprint != current_fingerprint:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Zendesk configuration changed after the preview was generated. "
                    "Refresh the dry-run plan, review it again, then re-approve deployment."
                ),
            )

        # Only after the fingerprint matches, zendesk_service.py applies dependencies and returns read-back results.
        status = zendesk_service.apply_setup(db, settings)
        if settings.zendesk_legacy_trigger_guard_enabled:
            brand_id = (status.get("ids") or {}).get("brand_id")
            if not isinstance(brand_id, int):
                raise zendesk_service.ZendeskError(
                    "Royal Tyres brand ID is unavailable for the legacy trigger safeguard.",
                    502,
                )
            # services/legacy_trigger_guard.py applies only allowlisted brand exclusions and checks preservation.
            guard_verification = legacy_trigger_guard.apply_exclusions(settings, brand_id)
            status = dict(status)
            status["verification"] = [
                *(status.get("verification") or []),
                *guard_verification,
            ]
            status["message"] = (
                f"{status.get('message', '').strip()} "
                "Confirmed legacy sandbox triggers are isolated from the Royal Tyres brand."
            ).strip()
            status = _with_legacy_guard_plan(status, settings)

        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error
