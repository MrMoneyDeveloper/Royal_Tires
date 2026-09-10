from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./asset_requests.db"
    app_username: str = ""
    app_password: SecretStr = SecretStr("")
    frontend_url: str = ""
    zendesk_subdomain: str = ""
    zendesk_email: str = ""
    zendesk_api_token: SecretStr = SecretStr("")
    zendesk_webhook_secret: SecretStr = SecretStr("")

    @field_validator("frontend_url")
    @classmethod
    def validate_origins(cls, value: str) -> str:
        for origin in filter(None, (part.strip() for part in value.split(","))):
            url = urlsplit(origin)
            if (url.scheme not in {"http", "https"} or not url.hostname or
                    url.username or url.password or url.path not in {"", "/"} or
                    url.query or url.fragment or "*" in origin):
                raise ValueError("FRONTEND_URL must contain explicit HTTP(S) origins")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [part.strip().rstrip("/") for part in self.frontend_url.split(",") if part.strip()]
