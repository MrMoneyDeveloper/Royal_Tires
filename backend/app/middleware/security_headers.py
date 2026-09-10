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
