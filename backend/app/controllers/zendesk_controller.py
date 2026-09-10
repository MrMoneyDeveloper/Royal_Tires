import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.database import get_db
from app.schemas import ZendeskApplyRequest, ZendeskSetupStatus
from app.services import zendesk_service

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


def _with_plan_fingerprint(status: dict) -> dict:
    status = dict(status)
    status["plan_fingerprint"] = _plan_fingerprint(status.get("plan") or [])
    return status


@router.get("/setup", response_model=ZendeskSetupStatus)
def get_setup(db: Database, request: Request):
    try:
        status = zendesk_service.get_setup_status(db, request.app.state.settings)
        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error


@router.post("/connect", response_model=ZendeskSetupStatus)
def connect(db: Database, request: Request):
    """Test Zendesk credentials already configured in the backend environment."""
    try:
        status = zendesk_service.connect(db, request.app.state.settings)
        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error


@router.post("/apply", response_model=ZendeskSetupStatus)
def apply_setup(data: ZendeskApplyRequest, db: Database, request: Request):
    if data.confirm is not True:
        raise HTTPException(
            status_code=400,
            detail="Explicit confirmation is required before Zendesk configuration is changed.",
        )
    try:
        # Re-read Zendesk immediately before mutation and refuse to deploy if the
        # current plan no longer matches the exact preview the admin approved.
        current = zendesk_service.get_setup_status(db, request.app.state.settings)
        current_fingerprint = _plan_fingerprint(current.get("plan") or [])
        if data.plan_fingerprint != current_fingerprint:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Zendesk configuration changed after the preview was generated. "
                    "Refresh the dry-run plan, review it again, then re-approve deployment."
                ),
            )

        status = zendesk_service.apply_setup(db, request.app.state.settings)
        return _with_plan_fingerprint(status)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error
