from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AssetRequestCreate, AssetRequestResponse
from app.services import request_service

router = APIRouter(prefix="/api/requests", tags=["Requests"])
Database = Annotated[Session, Depends(get_db)]


@router.post("", response_model=AssetRequestResponse, status_code=201)
def create_request(data: AssetRequestCreate, db: Database):
    return request_service.create_request(db, data)


@router.get("", response_model=list[AssetRequestResponse])
def list_requests(db: Database, limit: Annotated[int, Query(ge=1, le=100)] = 50,
                  offset: Annotated[int, Query(ge=0)] = 0):
    return request_service.list_requests(db, limit, offset)


@router.get("/{request_id}", response_model=AssetRequestResponse)
def get_request(request_id: int, db: Database):
    return request_service.get_request(db, request_id)
