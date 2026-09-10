"""
ROLE: HTTP middleware: response MIME/cache controls
CALLED BY: main registers it; FastAPI invokes it around requests
CALLS: call_next and response headers
DATA IN: Request path and downstream response
DATA OUT: nosniff header; no-store on /api/ responses
WHY: Apply the same response policy to all API routes.
SECURITY / RELIABILITY: X-Content-Type-Options: nosniff tells browsers not to infer another
    MIME type. Cache-Control: no-store asks caches not to store API responses. Neither is
    cookie protection or the reason an API is stateless.
FLOW: main registers it; FastAPI invokes it around requests -> this module -> call_next and
    response headers
"""

from fastapi import FastAPI, Request


def register_security_headers(app: FastAPI) -> None:
    """Apply response hardening consistently around the HTTP pipeline."""

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
