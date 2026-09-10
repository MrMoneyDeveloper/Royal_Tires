from pydantic import SecretStr
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
