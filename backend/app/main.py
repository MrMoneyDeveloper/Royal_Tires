"""
ROLE: Application composition root
CALLED BY: Uvicorn; tests via create_app
CALLS: Settings, Data package, middleware and Controllers
DATA IN: Optional typed Settings override
DATA OUT: FastAPI app, engine and session factory; public health/OpenAPI routes
WHY: Wire infrastructure once rather than in each business use case.
SECURITY / RELIABILITY: Lifespan creates missing tables and disposes the engine; create_all is
    not a migration system. Validation responses omit raw input; unexpected errors expose only
    a generic response.
FLOW: Uvicorn; tests via create_app -> this module -> Settings, Data package, middleware and
    Controllers
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers.request_controller import router as request_router
from app.controllers.webhook_controller import router as webhook_router
from app.controllers.zendesk_controller import router as zendesk_router
from app.core.config import Settings
from app.core.logging_config import configure_logging
from app.data import Base, create_db_engine, create_session_factory
from app.middleware import register_request_logging, register_security_headers
from app.services.request_service import RequestNotFound


def create_app(settings: Settings | None = None) -> FastAPI:
    # core/config.py reads Render environment values into typed Settings; tests may inject them.
    settings = settings or Settings()
    # data/db_context.py builds the shared Engine from DATABASE_URL, not from route input.
    engine = create_db_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        # Model mappings registered with data/base.py become SQL tables if missing; this is not a migration.
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="Royal Tyres IT Asset Requests",
        version="0.3.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    # data/session.py binds the factory once; get_db will yield a Session for each HTTP request.
    app.state.session_factory = create_session_factory(engine)

    # CORS checks browser origins; core/security.py separately authenticates business routes.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_request_logging(app)
    register_security_headers(app)

    # Hand matching URLs to controllers/*_controller.py after middleware and FastAPI dependencies.
    app.include_router(request_router)
    app.include_router(zendesk_router)
    app.include_router(webhook_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Return schema errors without echoing raw input values into the browser response.
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
