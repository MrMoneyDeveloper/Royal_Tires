from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.database import get_db
from app.schemas import ZendeskApplyRequest, ZendeskConnectRequest, ZendeskSetupStatus
from app.services import zendesk_service

router = APIRouter(
    prefix="/api/zendesk",
    tags=["Zendesk"],
    dependencies=[Depends(require_user)],
)

Database = Annotated[Session, Depends(get_db)]


def _translate(error: zendesk_service.ZendeskError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=str(error))


@router.get("/setup", response_model=ZendeskSetupStatus)
def get_setup(db: Database, request: Request):
    try:
        return zendesk_service.get_setup_status(db, request.app.state.settings)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error


@router.post("/connect", response_model=ZendeskSetupStatus)
def connect(data: ZendeskConnectRequest, db: Database, request: Request):
    try:
        return zendesk_service.connect(
            db,
            request.app.state.settings,
            data.subdomain,
            str(data.email),
            data.api_token.get_secret_value(),
        )
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
        return zendesk_service.apply_setup(db, request.app.state.settings)
    except zendesk_service.ZendeskError as error:
        raise _translate(error) from error
