"""
ROLE: Core configuration: environment to typed Settings
CALLED BY: main.create_app; tests may inject Settings
CALLS: Pydantic BaseSettings and origin validator
DATA IN: DATABASE_URL, APP_USERNAME, APP_PASSWORD, FRONTEND_URL; ZENDESK_SUBDOMAIN,
    ZENDESK_EMAIL, ZENDESK_API_TOKEN, ZENDESK_WEBHOOK_SECRET, ZENDESK_NOTIFICATION_EMAIL,
    RENDER_EXTERNAL_URL
DATA OUT: Typed settings consumed by Data, authentication, CORS and Zendesk
WHY: Runtime injection means the host supplies values when the app runs instead of hard-coding
    them into GitHub.
SECURITY / RELIABILITY: Host environment overrides local .env defaults. SecretStr masks normal
    secret display, but values must still never be logged; DATABASE_URL is also sensitive.
    Explicit CORS origins are validated. The legacy safeguard is opt-in.
FLOW: main.create_app; tests may inject Settings -> this module -> Pydantic BaseSettings and
    origin validator
"""

from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # BaseSettings loads runtime environment values, with .env for local use; main.py passes typed settings to other layers.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./asset_requests.db"
    app_username: str = ""
    app_password: SecretStr = SecretStr("")
    frontend_url: str = ""

    # Zendesk integration credentials are server-side environment variables.
    # They are never returned to the frontend or stored in PostgreSQL.
    zendesk_subdomain: str = ""
    zendesk_email: str = ""
    zendesk_api_token: SecretStr = SecretStr("")

    # Zendesk -> FastAPI status sync uses a separate bearer secret. Render
    # automatically supplies RENDER_EXTERNAL_URL for the public webhook endpoint.
    zendesk_webhook_secret: SecretStr = SecretStr("")
    zendesk_notification_email: str = "farhaanhotd1@gmail.com"
    render_external_url: str = ""

    # Opt-in because this safeguard updates pre-existing sandbox triggers rather
    # than only objects owned by this project.
    zendesk_legacy_trigger_guard_enabled: bool = False

    @field_validator("frontend_url")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in filter(None, (part.strip() for part in value.split(","))):
            url = urlsplit(origin)
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or url.username
                or url.password
                or url.path not in {"", "/"}
                or url.query
                or url.fragment
                or "*" in origin
            ):
                raise ValueError("FRONTEND_URL must contain explicit HTTP(S) origins")
        return value

    @property
    # main.py passes these validated origins to CORS middleware; they do not replace Basic Auth.
    def allowed_origins(self) -> list[str]:
        return [
            part.strip().rstrip("/")
            for part in self.frontend_url.split(",")
            if part.strip()
        ]