
from unittest.mock import Mock

import pytest
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

import nfc_hub.core.dependencies as dependencies_module
from nfc_hub.core.dependencies import get_current_session, get_db, require_authenticated_user, require_session, require_csrf_token, require_safe_auth_request
from nfc_hub.core.settings import AppSettings
from nfc_hub.models import Session, User


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



class TestRequiredSession:
    def test_returns_valid_session(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
        )

        result = require_session(session)

        assert result is session

    def test_raises_unauthorized_without_session(self):
        with pytest.raises(HTTPException) as exc_info:
            require_session(None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Valid session required"



class TestAuthenticatedUser:
    def test_returns_active_authenticated_user(self):
        user = User(
            id=7,
            email="user@example.com",
            password_hash="password-hash",
            is_active=True,
        )
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
            user_id=user.id,
            user=user,
        )

        result = require_authenticated_user(session)

        assert result is user

    def test_rejects_anonymous_session(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
            user_id=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            require_authenticated_user(session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    def test_rejects_session_without_loaded_user(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
            user_id=7,
            user=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            require_authenticated_user(session)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authentication required"

    def test_rejects_inactive_user(self):
        user = User(
            id=7,
            email="user@example.com",
            password_hash="password-hash",
            is_active=False,
        )
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="csrf-token",
            user_id=user.id,
            user=user,
        )

        with pytest.raises(HTTPException) as exc_info:
            require_authenticated_user(session)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "User account is inactive"



class TestCsrfProtection:
    def test_returns_session_for_matching_token(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="expected-csrf-token",
        )

        result = require_csrf_token(
            session,
            "expected-csrf-token",
        )

        assert result is session

    def test_rejects_missing_token(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="expected-csrf-token",
        )

        with pytest.raises(HTTPException) as exc_info:
            require_csrf_token(session, None)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Invalid CSRF token"

    def test_rejects_different_token(self):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="expected-csrf-token",
        )

        with pytest.raises(HTTPException) as exc_info:
            require_csrf_token(
                session,
                "different-csrf-token",
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Invalid CSRF token"

    def test_uses_timing_safe_verification(self, monkeypatch):
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="expected-csrf-token",
        )
        verify_mock = Mock(return_value=True)

        monkeypatch.setattr(
            dependencies_module,
            "verify_csrf_token",
            verify_mock,
        )

        require_csrf_token(
            session,
            "received-csrf-token",
        )

        verify_mock.assert_called_once_with(
            "received-csrf-token",
            "expected-csrf-token",
        )

    def test_reads_token_from_expected_header(self):
        test_app = FastAPI()
        session = Session(
            id=42,
            token_hash="a" * 64,
            csrf_token="expected-csrf-token",
        )

        test_app.dependency_overrides[require_session] = lambda: session

        @test_app.post("/protected")
        def protected_endpoint(
            current_session: Session = Depends(require_csrf_token),
        ):
            return {"session_id": current_session.id}

        test_client = TestClient(test_app)

        response = test_client.post(
            "/protected",
            headers={"X-CSRF-Token": "expected-csrf-token"},
        )

        assert response.status_code == 200
        assert response.json() == {"session_id": 42}



def make_auth_request(headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "headers": [
                (name.lower().encode("ascii"), value.encode("ascii"))
                for name, value in headers.items()
            ],
        }
    )


class TestSafeAuthRequest:
    @pytest.mark.parametrize(
        "headers",
        [
            {"Content-Type": "application/json"},
            {
                "Content-Type": "application/json",
                "Origin": "http://localhost:8000",
            },
            {
                "Content-Type": "application/json; charset=utf-8",
                "Origin": "http://localhost:8000",
            },
        ],
    )
    def test_accepts_safe_request(self, headers, monkeypatch):
        monkeypatch.setattr(
            dependencies_module,
            "get_settings",
            lambda: AppSettings(
                auth_allowed_origins=["http://localhost:8000"],
            ),
        )

        request = make_auth_request(headers)

        assert require_safe_auth_request(request) is None

    @pytest.mark.parametrize(
        "origin",
        [
            "https://evil.example",
            "null",
            "http://localhost:8000.evil.example",
        ],
    )
    def test_rejects_untrusted_origin(self, origin, monkeypatch):
        monkeypatch.setattr(
            dependencies_module,
            "get_settings",
            lambda: AppSettings(
                auth_allowed_origins=["http://localhost:8000"],
            ),
        )
        request = make_auth_request(
            {
                "Content-Type": "application/json",
                "Origin": origin,
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            require_safe_auth_request(request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Untrusted request origin"

    @pytest.mark.parametrize(
        "content_type",
        [
            "",
            "text/plain",
            "application/x-www-form-urlencoded",
        ],
    )
    def test_rejects_non_json_content_type(self, content_type):
        request = make_auth_request(
            {"Content-Type": content_type}
        )

        with pytest.raises(HTTPException) as exc_info:
            require_safe_auth_request(request)

        assert exc_info.value.status_code == 415
