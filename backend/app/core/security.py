import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic_auth = HTTPBasic(auto_error=False)


def require_user(
    request: Request,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic_auth)],
) -> str:
    settings = request.app.state.settings
    password = settings.app_password.get_secret_value()
    if not settings.app_username or not password:
        raise HTTPException(503, "Demo authentication is not configured.")
    username_ok = secrets.compare_digest(
        (credentials.username if credentials else "").encode(), settings.app_username.encode()
    )
    password_ok = secrets.compare_digest(
        (credentials.password if credentials else "").encode(), password.encode()
    )
    if not (username_ok and password_ok):
        raise HTTPException(401, "Invalid username or password.", headers={"WWW-Authenticate": "Basic"})
    return settings.app_username
