from sqlalchemy.orm import Session

from app.models.zendesk_connection import ZendeskConnection


def get_connection(db: Session) -> ZendeskConnection | None:
    return db.get(ZendeskConnection, 1)


def add_connection(db: Session, connection: ZendeskConnection) -> None:
    db.add(connection)
