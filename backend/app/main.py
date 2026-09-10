from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from app.controllers.request_controller import router as request_router
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

    app = FastAPI(title="Royal Tyres IT Asset Requests", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.include_router(request_router)

    @app.exception_handler(RequestNotFound)
    async def request_not_found(request: Request, exc: RequestNotFound):
        return JSONResponse(status_code=404, content={"detail": "Request not found."})

    @app.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
