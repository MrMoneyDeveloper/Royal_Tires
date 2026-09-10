from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_request import AssetRequest


def get_request(db: Session, request_id: int) -> AssetRequest | None:
    return db.get(AssetRequest, request_id)


def list_requests(db: Session, limit: int, offset: int) -> list[AssetRequest]:
    statement = select(AssetRequest).order_by(AssetRequest.created_at.desc(), AssetRequest.id.desc())
    return list(db.scalars(statement.limit(limit).offset(offset)))
