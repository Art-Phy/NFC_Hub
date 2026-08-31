
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import nfc_hub.core.dependencies as dependencies_module
from nfc_hub.core.dependencies import get_current_session, get_db
from nfc_hub.core.settings import AppSettings
from nfc_hub.models import Session


@pytest.fixture()
def fake_db():
    return Mock()


@pytest.fixture()
def app(fake_db):
    test_app = FastAPI()

    def override_get_db():
        yield fake_db

    test_app.dependency_overrides[get_db] = override_get_db

    @test_app.get("/session")
    def read_session(
        current_session: Session | None = Depends(get_current_session),
    ):
        if current_session is None:
            return {"session_id": None}

        return {"session_id": current_session.id}

    return test_app


@pytest.fixture()
def client(app):
    return TestClient(app)


class TestDatabaseDependency:
    def test_yields_database_session(self, monkeypatch):
        fake_database_session = Mock()
        session_factory = Mock(return_value=fake_database_session)

        monkeypatch.setattr(
            dependencies_module,
            "SessionLocal",
            session_factory,
        )

        dependency = get_db()

        yielded_session = next(dependency)

        assert yielded_session is fake_database_session
        session_factory.assert_called_once_with()

        with pytest.raises(StopIteration):
            next(dependency)

        fake_database_session.close.assert_called_once_with()

    def test_closes_database_session_when_dependency_is_closed(
        self,
        monkeypatch,
    ):
        fake_database_session = Mock()
        monkeypatch.setattr(
            dependencies_module,
            "SessionLocal",
            Mock(return_value=fake_database_session),
        )

        dependency = get_db()
        next(dependency)
        dependency.close()

        fake_database_session.close.assert_called_once_with()


class TestCurrentSessionDependency:
    def test_returns_none_when_cookie_is_missing(
        self,
        client,
        monkeypatch,
    ):
        get_valid_session_mock = Mock()
        monkeypatch.setattr(
            dependencies_module,
            "get_valid_session",
            get_valid_session_mock,
        )

        response = client.get("/session")

        assert response.status_code == 200
        assert response.json() == {"session_id": None}
        get_valid_session_mock.assert_not_called()

    def test_resolves_session_from_configured_cookie(
        self,
        client,
        fake_db,
        monkeypatch,
    ):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
        )
        get_valid_session_mock = Mock(return_value=session)

        monkeypatch.setattr(
            dependencies_module,
            "get_valid_session",
            get_valid_session_mock,
        )
        monkeypatch.setattr(
            dependencies_module,
            "get_settings",
            lambda: AppSettings(session_cookie_name="custom-session"),
        )

        client.cookies.set(
            "custom-session",
            "raw-session-token",
        )

        response = client.get("/session")

        assert response.status_code == 200
        assert response.json() == {"session_id": 42}
        get_valid_session_mock.assert_called_once_with(
            fake_db,
            "raw-session-token",
        )

    def test_returns_none_for_invalid_session_token(
        self,
        client,
        fake_db,
        monkeypatch,
    ):
        get_valid_session_mock = Mock(return_value=None)
        monkeypatch.setattr(
            dependencies_module,
            "get_valid_session",
            get_valid_session_mock,
        )

        settings = AppSettings()
        client.cookies.set(
            settings.session_cookie_name,
            "invalid-session-token",
        )

        response = client.get("/session")

        assert response.status_code == 200
        assert response.json() == {"session_id": None}
        get_valid_session_mock.assert_called_once_with(
            fake_db,
            "invalid-session-token",
        )
