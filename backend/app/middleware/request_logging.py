"""
ROLE: HTTP middleware: safe response-path request logging
CALLED BY: main registers it; FastAPI invokes it around requests
CALLS: call_next then app.http logger
DATA IN: HTTP method, matched route template and returned status
DATA OUT: Unchanged response plus safe log entry
WHY: Observe endpoint outcomes without copying request bodies or credentials.
SECURITY / RELIABILITY: Request enters, continues toward Controller, and returning response is
    logged. Current implementation records method/route/status only, not elapsed timing, query
    strings or Authorization headers.
FLOW: main registers it; FastAPI invokes it around requests -> this module -> call_next then
    app.http logger
"""

import logging

from fastapi import FastAPI, Request


def register_request_logging(app: FastAPI) -> None:
    """Log method, matched route and response status without logging secrets."""

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        # Continue through FastAPI dependencies and the matched Controller; its response comes back through this middleware.
        response = await call_next(request)
        route = request.scope.get("route")
        # On the return path, log method/route/status only; never copy Authorization headers or request bodies.
        logging.getLogger("app.http").info(
            "method=%s route=%s status=%s",
            request.method,
            getattr(route, "path", "unmatched"),
            response.status_code,
        )
        return response
