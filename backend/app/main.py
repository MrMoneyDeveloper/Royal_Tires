from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from app.controllers.request_controller import router as request_router
from app.controllers.zendesk_controller import router as zendesk_router
from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.database import Base, create_db_engine
from app.services.request_service import RequestNotFound


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = create_db_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Royal Tyres IT Asset Requests", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(request_router)
    app.include_router(zendesk_router)

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
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        errors = [
            {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logging.getLogger("app.errors").error(
            "Unhandled error type=%s", type(exc).__name__
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred."},
        )

    @app.exception_handler(RequestNotFound)
    async def request_not_found(request: Request, exc: RequestNotFound):
        return JSONResponse(status_code=404, content={"detail": "Request not found."})

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
