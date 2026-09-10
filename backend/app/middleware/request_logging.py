import logging

from fastapi import FastAPI, Request


def register_request_logging(app: FastAPI) -> None:
    """Log method, matched route and response status without logging secrets."""

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        response = await call_next(request)
        route = request.scope.get("route")
        logging.getLogger("app.http").info(
            "method=%s route=%s status=%s",
            request.method,
            getattr(route, "path", "unmatched"),
            response.status_code,
        )
        return response
