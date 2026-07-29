import pytest

from nfc_hub.core.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestDefaults:
    def test_app_name_default(self):
        settings = get_settings()
        assert settings.app_name == "NFC Hub"

    def test_environment_default(self):
        settings = get_settings()
        assert settings.environment == "development"

    def test_debug_default(self):
        settings = get_settings()
        assert settings.debug is False

    def test_version_from_package(self):
        settings = get_settings()
        assert isinstance(settings.version, str)
        assert settings.version != ""


class TestEnvOverrides:
    def test_app_name_override(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_APP_NAME", "Test App")
        settings = get_settings()
        assert settings.app_name == "Test App"

    def test_environment_override(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_ENVIRONMENT", "testing")
        settings = get_settings()
        assert settings.environment == "testing"

    def test_debug_override(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_DEBUG", "true")
        settings = get_settings()
        assert settings.debug is True
