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
    dependencies=[Depends(require_user)],
)
Database = Annotated[Session, Depends(get_db)]


@router.post("", response_model=AssetRequestResponse, status_code=201)
def create_request(data: AssetRequestCreate, db: Database, request: Request):
    return request_service.create_request(db, data, request.app.state.settings)


@router.get("", response_model=list[AssetRequestResponse])
def list_requests(
    db: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return request_service.list_requests(db, limit, offset)


@router.get("/{request_id}", response_model=AssetRequestResponse)
def get_request(request_id: int, db: Database):
    return request_service.get_request(db, request_id)
