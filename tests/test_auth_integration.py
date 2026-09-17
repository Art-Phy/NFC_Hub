
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from nfc_hub.core.database import Base, build_engine
from nfc_hub.core.dependencies import get_db
from nfc_hub.core.passwords import verify_password
from nfc_hub.core.settings import get_settings
from nfc_hub.core.tokens import hash_session_token
from nfc_hub.main import app
from nfc_hub.models import Session, User


REGISTRATION_DATA = {
    "email": "user@example.com",
    "password": "secure-integration-password",
}


@pytest.fixture()
def session_factory(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'auth_integration.db'}"
    test_engine = build_engine(database_url)
    Base.metadata.create_all(test_engine)

    factory = sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
    )

    try:
        yield factory
    finally:
        test_engine.dispose()


@pytest.fixture()
def client(session_factory, monkeypatch):
    monkeypatch.setenv("NFC_HUB_ENVIRONMENT", "development")
    monkeypatch.setenv("NFC_HUB_SESSION_COOKIE_SECURE", "false")
    get_settings.cache_clear()

    def override_get_db():
        db = session_factory()

        try:
            yield db
        finally:
            db.close()

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


def register(client):
    response = client.post(
        "/auth/register",
        json=REGISTRATION_DATA,
    )

    assert response.status_code == 201, response.text

    return response


class TestAuthenticationIntegration:
    def test_registration_creates_user_and_valid_session(
        self,
        client,
        session_factory,
    ):
        registration = register(client)
        cookie_name = get_settings().session_cookie_name
        session_token = client.cookies.get(cookie_name)

        assert session_token is not None

        current_user = client.get("/auth/me")

        assert current_user.status_code == 200
        assert current_user.json() == registration.json()

        with session_factory() as db:
            user = db.execute(select(User)).scalar_one()
            session = db.execute(select(Session)).scalar_one()

            assert user.email == REGISTRATION_DATA["email"]
            assert verify_password(
                REGISTRATION_DATA["password"],
                user.password_hash,
            )
            assert user.password_hash != REGISTRATION_DATA["password"]
            assert session.user_id == user.id
            assert session.token_hash == hash_session_token(session_token)
            assert session.token_hash != session_token
            assert session.csrf_token == registration.json()["csrf_token"]

    def test_logout_deletes_session_and_removes_cookie(
        self,
        client,
        session_factory,
    ):
        registration = register(client)
        cookie_name = get_settings().session_cookie_name

        response = client.post(
            "/auth/logout",
            headers={
                "X-CSRF-Token": registration.json()["csrf_token"],
            },
        )

        assert response.status_code == 204
        assert response.content == b""
        assert client.cookies.get(cookie_name) is None
        assert client.get("/auth/me").status_code == 401

        with session_factory() as db:
            assert db.execute(select(Session)).scalar_one_or_none() is None
            assert db.execute(select(User)).scalar_one_or_none() is not None

    def test_revoked_session_token_cannot_be_reused(self, client):
        registration = register(client)
        cookie_name = get_settings().session_cookie_name
        original_token = client.cookies.get(cookie_name)

        assert original_token is not None

        logout = client.post(
            "/auth/logout",
            headers={
                "X-CSRF-Token": registration.json()["csrf_token"],
            },
        )

        assert logout.status_code == 204

        client.cookies.set(cookie_name, original_token)

        response = client.get("/auth/me")

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Valid session required"
        }

    def test_login_creates_new_session_after_logout(
        self,
        client,
        session_factory,
    ):
        registration = register(client)
        cookie_name = get_settings().session_cookie_name
        original_token = client.cookies.get(cookie_name)

        logout = client.post(
            "/auth/logout",
            headers={
                "X-CSRF-Token": registration.json()["csrf_token"],
            },
        )

        assert logout.status_code == 204

        login = client.post(
            "/auth/login",
            json=REGISTRATION_DATA,
        )

        assert login.status_code == 200
        assert login.json()["user"] == registration.json()["user"]
        assert client.cookies.get(cookie_name) is not None
        assert client.cookies.get(cookie_name) != original_token
        assert login.json()["csrf_token"] != registration.json()["csrf_token"]

        current_user = client.get("/auth/me")

        assert current_user.status_code == 200
        assert current_user.json() == login.json()

        with session_factory() as db:
            sessions = db.execute(select(Session)).scalars().all()

            assert len(sessions) == 1

    def test_duplicate_registration_does_not_create_extra_records(
        self,
        client,
        session_factory,
    ):
        register(client)

        response = client.post(
            "/auth/register",
            json={
                "email": "USER@EXAMPLE.COM",
                "password": "another-secure-password",
            },
        )

        assert response.status_code == 409

        with session_factory() as db:
            users = db.execute(select(User)).scalars().all()
            sessions = db.execute(select(Session)).scalars().all()

            assert len(users) == 1
            assert len(sessions) == 1

    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {"X-CSRF-Token": "incorrect-csrf-token"},
        ],
        ids=["missing-csrf", "incorrect-csrf"],
    )
    def test_invalid_csrf_preserves_current_session(
        self,
        client,
        session_factory,
        headers,
    ):
        registration = register(client)
        cookie_name = get_settings().session_cookie_name
        original_token = client.cookies.get(cookie_name)

        response = client.post(
            "/auth/logout",
            headers=headers,
        )

        assert response.status_code == 403
        assert client.cookies.get(cookie_name) == original_token

        current_user = client.get("/auth/me")

        assert current_user.status_code == 200
        assert current_user.json() == registration.json()

        with session_factory() as db:
            assert db.execute(select(Session)).scalar_one_or_none() is not None

    def test_invalid_password_does_not_create_session(
        self,
        client,
        session_factory,
    ):
        registration = register(client)

        logout = client.post(
            "/auth/logout",
            headers={
                "X-CSRF-Token": registration.json()["csrf_token"],
            },
        )

        assert logout.status_code == 204

        response = client.post(
            "/auth/login",
            json={
                "email": REGISTRATION_DATA["email"],
                "password": "incorrect-password",
            },
        )

        assert response.status_code == 401
        assert client.get("/auth/me").status_code == 401

        with session_factory() as db:
            assert db.execute(select(Session)).scalar_one_or_none() is None
