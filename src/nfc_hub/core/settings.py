
from functools import lru_cache
from importlib.metadata import version as pkg_version

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NFC_HUB_")

    app_name: str = "NFC Hub"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./nfc_hub.db"

    session_cookie_name: str = "nfc_hub_session"
    session_cookie_secure: bool = False
    authenticated_session_ttl_seconds: int = 2_592_000
    anonymous_session_ttl_seconds: int = 900

    @model_validator(mode="after")
    def validate_production_cookie_security(self) -> "AppSettings":
        if (
            self.environment.strip().lower() == "production"
            and not self.session_cookie_secure
        ):
            raise ValueError(
                "Secure session cookies must be enabled in production"
            )

        return self


    @property
    def version(self) -> str:
        return pkg_version("nfc-hub")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
