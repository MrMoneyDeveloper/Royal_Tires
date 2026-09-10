from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
    def allowed_origins(self) -> list[str]:
        return [
            part.strip().rstrip("/")
            for part in self.frontend_url.split(",")
            if part.strip()
        ]
