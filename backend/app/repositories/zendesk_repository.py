"""
ROLE: Zendesk metadata Repository: singleton add/get helpers
CALLED BY: ZendeskService
CALLS: ZendeskConnection and supplied Session
DATA IN: Session and optional connection entity
DATA OUT: Singleton metadata record or pending added entity
WHY: Express metadata persistence operations separately from external HTTP.
SECURITY / RELIABILITY: No token persistence or independent connection creation.
    ZendeskService owns when metadata is saved and committed; this repository owns add/get
    operations.
FLOW: ZendeskService -> this module -> ZendeskConnection and supplied Session
"""

from sqlalchemy.orm import Session

from app.models.zendesk_connection import ZendeskConnection


def get_connection(db: Session) -> ZendeskConnection | None:
    # models/zendesk_connection.py stores singleton metadata at local ID 1; this is a database read, not Zendesk HTTP.
    return db.get(ZendeskConnection, 1)


def add_connection(db: Session, connection: ZendeskConnection) -> None:
    # Stage safe metadata using the injected Session; zendesk_service.py commits after its workflow checks.
    db.add(connection)
