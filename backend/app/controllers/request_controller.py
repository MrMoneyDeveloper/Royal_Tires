"""
ROLE: Request Controller: HTTP boundary for create/list/detail
CALLED BY: React api.js through /api/requests
CALLS: RequestService; FastAPI schema/auth/session dependencies
DATA IN: Basic-authenticated request, AssetRequestCreate or bounded pagination
DATA OUT: AssetRequestResponse JSON; create returns HTTP 201
WHY: Keep HTTP routing separate from business sequencing and SQL.
SECURITY / RELIABILITY: FastAPI validates Pydantic input before the route function runs. All
    three routes require Basic Auth; no direct SQL or Zendesk calls.
FLOW: React api.js through /api/requests -> this module -> RequestService; FastAPI
    schema/auth/session dependencies
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.security import require_user
from app.data.session import get_db
from app.schemas.request_schema import AssetRequestCreate, AssetRequestResponse
from app.services import request_service

router = APIRouter(
    prefix="/api/requests",
    tags=["Requests"],
    # core/security.py checks Basic Auth before any business route body executes.
    dependencies=[Depends(require_user)],
)
# data/session.py supplies the shared request-scoped Session; this Controller does not create connections.
Database = Annotated[Session, Depends(get_db)]


# request_schema.py validates incoming JSON before this function; its response schema serializes the returned Model.
@router.post("", response_model=AssetRequestResponse, status_code=201)
def create_request(data: AssetRequestCreate, db: Database, request: Request):
    # services/request_service.py owns persistence/Zendesk sequencing and returns the saved AssetRequest.
    return request_service.create_request(db, data, request.app.state.settings)


@router.get("", response_model=list[AssetRequestResponse])
def list_requests(
    db: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    # request_service.py delegates the bounded query to request_repository.py and returns Models for serialization.
    return request_service.list_requests(db, limit, offset)


@router.get("/{request_id}", response_model=AssetRequestResponse)
def get_request(request_id: int, db: Database):
    # request_service.py returns the local Model or raises RequestNotFound, mapped to HTTP 404 in main.py.
    return request_service.get_request(db, request_id)
