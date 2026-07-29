from functools import lru_cache
from importlib.metadata import version as pkg_version

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NFC_HUB_")

    app_name: str = "NFC Hub"
    environment: str = "development"
    debug: bool = False

    @property
    def version(self) -> str:
        return pkg_version("nfc-hub")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
