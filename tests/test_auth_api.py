
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import nfc_hub.api.auth as auth_api
from nfc_hub.core.auth_service import EmailAlreadyRegisteredError, InvalidCredentialsError
from nfc_hub.core.dependencies import get_db, require_csrf_token, require_session, require_authenticated_user
from nfc_hub.core.session_service import CreatedSession
from nfc_hub.main import app
from nfc_hub.models import Session, User


@pytest.fixture()
def fake_db():
    return Mock()


@pytest.fixture()
def client(fake_db):
    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user():
    return User(
        id=42,
        email="user@example.com",
        password_hash="password-hash",
        is_active=True,
    )


@pytest.fixture()
def created_session():
    return CreatedSession(
        session=Session(
            id=7,
            token_hash="a" * 64,
            csrf_token="csrf-token",
            user_id=42,
        ),
        session_token="raw-session-token",
        csrf_token="csrf-token",
    )


class TestRegisterEndpoint:
    def test_registers_user_and_returns_authentication_data(
        self,
        client,
        fake_db,
        registered_user,
        created_session,
        monkeypatch,
    ):
        register_mock = Mock(return_value=registered_user)
        create_session_mock = Mock(return_value=created_session)

        monkeypatch.setattr(
            auth_api,
            "register_user",
            register_mock,
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            create_session_mock,
        )

        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        assert response.status_code == 201
        assert response.headers["cache-control"] == "no-store"
        assert response.json() == {
            "user": {
                "id": 42,
                "email": "user@example.com",
            },
            "csrf_token": "csrf-token",
        }
        register_mock.assert_called_once_with(
            fake_db,
            email="user@example.com",
            password="secure-password",
        )
        create_session_mock.assert_called_once_with(
            fake_db,
            user_id=42,
        )
        fake_db.commit.assert_called_once_with()
        fake_db.refresh.assert_called_once_with(registered_user)

    def test_sets_session_token_in_httponly_cookie(
        self,
        client,
        registered_user,
        created_session,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "register_user",
            Mock(return_value=registered_user),
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            Mock(return_value=created_session),
        )

        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        cookie_header = response.headers["set-cookie"]

        assert "nfc_hub_session=raw-session-token" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert "Path=/" in cookie_header
        assert "Max-Age=2592000" in cookie_header

    def test_does_not_expose_session_token_in_response(
        self,
        client,
        registered_user,
        created_session,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "register_user",
            Mock(return_value=registered_user),
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            Mock(return_value=created_session),
        )

        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        assert "raw-session-token" not in response.text
        assert "password-hash" not in response.text

    def test_returns_conflict_for_registered_email(
        self,
        client,
        fake_db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "register_user",
            Mock(
                side_effect=EmailAlreadyRegisteredError(
                    "Email address is already registered"
                )
            ),
        )

        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "Email address is already registered"
        }
        fake_db.rollback.assert_called_once_with()
        fake_db.commit.assert_not_called()

    def test_rolls_back_when_session_creation_fails(
        self,
        client,
        fake_db,
        registered_user,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "register_user",
            Mock(return_value=registered_user),
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            Mock(side_effect=RuntimeError("database failure")),
        )

        with pytest.raises(RuntimeError, match="database failure"):
            client.post(
                "/auth/register",
                json={
                    "email": "user@example.com",
                    "password": "secure-password",
                },
            )

        fake_db.rollback.assert_called_once_with()
        fake_db.commit.assert_not_called()

    def test_rejects_invalid_request_before_using_database(
        self,
        client,
        fake_db,
    ):
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "password": "short",
            },
        )

        assert response.status_code == 422
        fake_db.commit.assert_not_called()



class TestLoginEndpoint:
    def test_authenticates_user_and_returns_session_data(
        self,
        client,
        fake_db,
        registered_user,
        created_session,
        monkeypatch,
    ):
        authenticate_mock = Mock(return_value=registered_user)
        create_session_mock = Mock(return_value=created_session)

        monkeypatch.setattr(
            auth_api,
            "authenticate_user",
            authenticate_mock,
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            create_session_mock,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json() == {
            "user": {
                "id": 42,
                "email": "user@example.com",
            },
            "csrf_token": "csrf-token",
        }
        authenticate_mock.assert_called_once_with(
            fake_db,
            email="user@example.com",
            password="secure-password",
        )
        create_session_mock.assert_called_once_with(
            fake_db,
            user_id=42,
        )
        fake_db.commit.assert_called_once_with()
        fake_db.refresh.assert_called_once_with(registered_user)

    def test_sets_session_cookie(
        self,
        client,
        registered_user,
        created_session,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "authenticate_user",
            Mock(return_value=registered_user),
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            Mock(return_value=created_session),
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "secure-password",
            },
        )

        cookie_header = response.headers["set-cookie"]

        assert "nfc_hub_session=raw-session-token" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert "Path=/" in cookie_header

    def test_returns_unauthorized_for_invalid_credentials(
        self,
        client,
        fake_db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "authenticate_user",
            Mock(
                side_effect=InvalidCredentialsError(
                    "Invalid email or password"
                )
            ),
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "incorrect-password",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password"
        }
        fake_db.rollback.assert_called_once_with()
        fake_db.commit.assert_not_called()

    def test_rolls_back_when_session_creation_fails(
        self,
        client,
        fake_db,
        registered_user,
        monkeypatch,
    ):
        monkeypatch.setattr(
            auth_api,
            "authenticate_user",
            Mock(return_value=registered_user),
        )
        monkeypatch.setattr(
            auth_api,
            "create_session",
            Mock(side_effect=RuntimeError("database failure")),
        )

        with pytest.raises(RuntimeError, match="database failure"):
            client.post(
                "/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "secure-password",
                },
            )

        fake_db.rollback.assert_called_once_with()
        fake_db.commit.assert_not_called()

    def test_rejects_invalid_request_before_authentication(
        self,
        client,
        fake_db,
        monkeypatch,
    ):
        authenticate_mock = Mock()
        monkeypatch.setattr(
            auth_api,
            "authenticate_user",
            authenticate_mock,
        )

        response = client.post(
            "/auth/login",
            json={
                "email": "invalid-email",
                "password": "",
            },
        )

        assert response.status_code == 422
        authenticate_mock.assert_not_called()
        fake_db.commit.assert_not_called()



class TestLogoutEndpoint:
    def test_deletes_current_session(
        self,
        client,
        fake_db,
        created_session,
        monkeypatch,
    ):
        delete_session_mock = Mock(return_value=True)

        app.dependency_overrides[require_csrf_token] = (
            lambda: created_session.session
        )
        monkeypatch.setattr(
            auth_api,
            "delete_session",
            delete_session_mock,
        )
        client.cookies.set(
            "nfc_hub_session",
            "raw-session-token",
        )

        response = client.post("/auth/logout")

        assert response.status_code == 204
        assert response.headers["cache-control"] == "no-store"
        assert response.content == b""
        delete_session_mock.assert_called_once_with(
            fake_db,
            "raw-session-token",
        )
        fake_db.commit.assert_called_once_with()
        fake_db.rollback.assert_not_called()

    def test_removes_session_cookie(
        self,
        client,
        created_session,
        monkeypatch,
    ):
        app.dependency_overrides[require_csrf_token] = (
            lambda: created_session.session
        )
        monkeypatch.setattr(
            auth_api,
            "delete_session",
            Mock(return_value=True),
        )
        client.cookies.set(
            "nfc_hub_session",
            "raw-session-token",
        )

        response = client.post("/auth/logout")

        cookie_header = response.headers["set-cookie"]

        assert "nfc_hub_session=" in cookie_header
        assert "Max-Age=0" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "SameSite=lax" in cookie_header
        assert "Path=/" in cookie_header

    def test_requires_csrf_token(
        self,
        client,
        fake_db,
        created_session,
        monkeypatch,
    ):
        app.dependency_overrides[require_session] = (
            lambda: created_session.session
        )
        delete_session_mock = Mock(return_value=True)
        monkeypatch.setattr(
            auth_api,
            "delete_session",
            delete_session_mock,
        )
        client.cookies.set(
            "nfc_hub_session",
            "raw-session-token",
        )

        response = client.post("/auth/logout")

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Invalid CSRF token"
        }
        delete_session_mock.assert_not_called()
        fake_db.commit.assert_not_called()

    def test_rolls_back_when_session_deletion_fails(
        self,
        client,
        fake_db,
        created_session,
        monkeypatch,
    ):
        app.dependency_overrides[require_csrf_token] = (
            lambda: created_session.session
        )
        monkeypatch.setattr(
            auth_api,
            "delete_session",
            Mock(side_effect=RuntimeError("database failure")),
        )
        client.cookies.set(
            "nfc_hub_session",
            "raw-session-token",
        )

        with pytest.raises(RuntimeError, match="database failure"):
            client.post("/auth/logout")

        fake_db.rollback.assert_called_once_with()
        fake_db.commit.assert_not_called()



class TestCurrentUserEndpoint:
    def test_returns_authenticated_user_and_csrf_token(
        self,
        client,
        fake_db,
        registered_user,
        created_session,
    ):
        app.dependency_overrides[require_authenticated_user] = (
            lambda: registered_user
        )
        app.dependency_overrides[require_session] = (
            lambda: created_session.session
        )

        response = client.get("/auth/me")

        assert response.status_code == 200
        assert response.json() == {
            "user": {
                "id": 42,
                "email": "user@example.com",
            },
            "csrf_token": "csrf-token",
        }
        assert response.headers["cache-control"] == "no-store"
        fake_db.commit.assert_not_called()

    def test_rejects_request_without_session(self, client):
        response = client.get("/auth/me")

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Valid session required"
        }

    def test_rejects_anonymous_session(
        self,
        client,
    ):
        anonymous_session = Session(
            id=8,
            token_hash="b" * 64,
            csrf_token="anonymous-csrf-token",
            user_id=None,
        )
        app.dependency_overrides[require_session] = (
            lambda: anonymous_session
        )

        response = client.get("/auth/me")

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Authentication required"
        }

    def test_rejects_inactive_user(
        self,
        client,
        registered_user,
        created_session,
    ):
        registered_user.is_active = False
        created_session.session.user = registered_user

        app.dependency_overrides[require_session] = (
            lambda: created_session.session
        )

        response = client.get("/auth/me")

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User account is inactive"
        }

    def test_does_not_expose_session_token_or_password_hash(
        self,
        client,
        registered_user,
        created_session,
    ):
        app.dependency_overrides[require_authenticated_user] = (
            lambda: registered_user
        )
        app.dependency_overrides[require_session] = (
            lambda: created_session.session
        )

        response = client.get("/auth/me")

        assert response.status_code == 200
        assert "raw-session-token" not in response.text
        assert "password_hash" not in response.json()["user"]
