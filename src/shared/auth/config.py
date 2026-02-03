from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # JWT Configuration
    secret_key: str = Field(validation_alias="secret_key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)

    # Authorization Code Configuration
    authorization_code_expire_minutes: int = Field(default=10)

    # OAuth Client Configuration
    oauth_client_id: str = Field(validation_alias="oauth_client_id")
    oauth_redirect_uri: str = Field(validation_alias="oauth_redirect_uri")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="auth_",
        extra="ignore",
    )


settings = Settings()
