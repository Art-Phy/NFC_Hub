
import pytest
from pydantic import ValidationError

from nfc_hub.core.settings import get_settings, AppSettings


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

    def test_session_cookie_name_default(self):
        settings = get_settings()

        assert settings.session_cookie_name == "nfc_hub_session"

    def test_session_cookie_secure_default(self):
        settings = get_settings()

        assert settings.session_cookie_secure is False

    def test_authenticated_session_ttl_default(self):
        settings = get_settings()

        assert settings.authenticated_session_ttl_seconds == 2_592_000

    def test_anonymous_session_ttl_default(self):
        settings = get_settings()

        assert settings.anonymous_session_ttl_seconds == 900


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

    def test_session_cookie_name_override(self, monkeypatch):
        monkeypatch.setenv(
            "NFC_HUB_SESSION_COOKIE_NAME",
            "custom_session",
        )

        settings = get_settings()

        assert settings.session_cookie_name == "custom_session"

    def test_session_cookie_secure_override(self, monkeypatch):
        monkeypatch.setenv(
            "NFC_HUB_SESSION_COOKIE_SECURE",
            "true",
        )

        settings = get_settings()

        assert settings.session_cookie_secure is True

    def test_authenticated_session_ttl_override(self, monkeypatch):
        monkeypatch.setenv(
            "NFC_HUB_AUTHENTICATED_SESSION_TTL_SECONDS",
            "3600",
        )

        settings = get_settings()

        assert settings.authenticated_session_ttl_seconds == 3600

    def test_anonymous_session_ttl_override(self, monkeypatch):
        monkeypatch.setenv(
            "NFC_HUB_ANONYMOUS_SESSION_TTL_SECONDS",
            "300",
        )

        settings = get_settings()

        assert settings.anonymous_session_ttl_seconds == 300


class TestProductionSecurity:
    def test_production_accepts_secure_session_cookies(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_ENVIRONMENT", "production")
        monkeypatch.setenv(
            "NFC_HUB_SESSION_COOKIE_SECURE",
            "true",
        )

        settings = get_settings()

        assert settings.session_cookie_secure is True

    def test_production_rejects_insecure_session_cookies(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_ENVIRONMENT", "production")
        monkeypatch.setenv(
            "NFC_HUB_SESSION_COOKIE_SECURE",
            "false",
        )

        with pytest.raises(
            ValidationError,
            match="Secure session cookies must be enabled in production",
        ):
            get_settings()


class TestDatabaseUrl:
    def test_default_database_url(self):
        settings = get_settings()

        assert settings.database_url == "sqlite:///./nfc_hub.db"

    def test_database_url_override(self, monkeypatch):
        monkeypatch.setenv(
            "NFC_HUB_DATABASE_URL",
            "sqlite:///./custom.db",
        )

        settings = get_settings()

        assert settings.database_url == "sqlite:///./custom.db"



class TestSessionTtlValidation:
    @pytest.mark.parametrize(
        "field_name",
        [
            "authenticated_session_ttl_seconds",
            "anonymous_session_ttl_seconds",
        ],
    )
    @pytest.mark.parametrize("ttl", [0, -1])
    def test_rejects_non_positive_ttl(self, field_name, ttl):
        with pytest.raises(ValidationError):
            AppSettings(**{field_name: ttl})

    @pytest.mark.parametrize(
        "field_name",
        [
            "authenticated_session_ttl_seconds",
            "anonymous_session_ttl_seconds",
        ],
    )
    def test_accepts_positive_ttl(self, field_name):
        settings = AppSettings(**{field_name: 1})

        assert getattr(settings, field_name) == 1
