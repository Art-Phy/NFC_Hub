
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import nfc_hub.core.session_service as service_module
from nfc_hub.core.database import Base
from nfc_hub.core.session_service import CreatedSession, create_session, get_valid_session
from nfc_hub.core.settings import AppSettings
from nfc_hub.core.tokens import hash_session_token
from nfc_hub.models import Session, User


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    database_session = session_factory()

    try:
        yield database_session
    finally:
        database_session.close()
        engine.dispose()


@pytest.fixture()
def fixed_now():
    return datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def fixed_tokens(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "generate_session_token",
        lambda: "raw-session-token",
    )
    monkeypatch.setattr(
        service_module,
        "generate_csrf_token",
        lambda: "csrf-token",
    )


class TestAnonymousSessionCreation:
    def test_creates_anonymous_session(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(anonymous_session_ttl_seconds=900)

        result = create_session(db, settings=settings)

        assert isinstance(result, CreatedSession)
        assert result.session.id is not None
        assert result.session.user_id is None
        assert result.session_token == "raw-session-token"
        assert result.csrf_token == "csrf-token"
        assert result.session.expires_at == fixed_now + timedelta(minutes=15)

    def test_stores_hash_instead_of_raw_session_token(
        self,
        db,
        fixed_tokens,
    ):
        result = create_session(db)

        stored_session = db.execute(select(Session)).scalar_one()

        assert stored_session.id == result.session.id
        assert stored_session.token_hash == hash_session_token(
            "raw-session-token"
        )
        assert stored_session.token_hash != "raw-session-token"

    def test_stores_csrf_token(self, db, fixed_tokens):
        create_session(db)

        stored_session = db.execute(select(Session)).scalar_one()

        assert stored_session.csrf_token == "csrf-token"


class TestAuthenticatedSessionCreation:
    def test_creates_session_for_user(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(
            authenticated_session_ttl_seconds=2_592_000,
        )
        user = User(
            email="user@example.com",
            password_hash="password-hash",
        )
        db.add(user)
        db.flush()

        result = create_session(
            db,
            user_id=user.id,
            settings=settings,
        )

        assert result.session.user_id == user.id
        assert result.session.expires_at == fixed_now + timedelta(days=30)

    def test_authenticated_session_uses_authenticated_ttl(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(
            anonymous_session_ttl_seconds=60,
            authenticated_session_ttl_seconds=120,
        )
        user = User(
            email="user@example.com",
            password_hash="password-hash",
        )
        db.add(user)
        db.flush()

        result = create_session(
            db,
            user_id=user.id,
            settings=settings,
        )

        assert result.session.expires_at == fixed_now + timedelta(seconds=120)



class TestSessionLookup:
    def test_returns_session_for_valid_token(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        created = create_session(db)
        db.commit()
        db.expire_all()

        session = get_valid_session(db, created.session_token)

        assert session is not None
        assert session.id == created.session.id

    def test_returns_none_for_unknown_token(
        self,
        db,
        fixed_tokens,
    ):
        create_session(db)
        db.commit()

        session = get_valid_session(db, "unknown-session-token")

        assert session is None

    def test_returns_none_for_different_token(
        self,
        db,
        fixed_tokens,
    ):
        created = create_session(db)
        db.commit()

        session = get_valid_session(
            db,
            f"{created.session_token}-modified",
        )

        assert session is None


class TestSessionExpiration:
    def test_returns_none_for_expired_session(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(anonymous_session_ttl_seconds=60)
        created = create_session(db, settings=settings)
        db.commit()
        db.expire_all()

        monkeypatch.setattr(
            service_module,
            "_utc_now",
            lambda: fixed_now + timedelta(seconds=61),
        )

        session = get_valid_session(db, created.session_token)

        assert session is None

    def test_session_is_invalid_at_exact_expiration_time(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(anonymous_session_ttl_seconds=60)
        created = create_session(db, settings=settings)
        db.commit()
        db.expire_all()

        monkeypatch.setattr(
            service_module,
            "_utc_now",
            lambda: fixed_now + timedelta(seconds=60),
        )

        session = get_valid_session(db, created.session_token)

        assert session is None

    def test_session_is_valid_just_before_expiration(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        settings = AppSettings(anonymous_session_ttl_seconds=60)
        created = create_session(db, settings=settings)
        db.commit()
        db.expire_all()

        monkeypatch.setattr(
            service_module,
            "_utc_now",
            lambda: fixed_now + timedelta(seconds=59),
        )

        session = get_valid_session(db, created.session_token)

        assert session is not None

    def test_handles_naive_datetime_loaded_from_sqlite(
        self,
        db,
        monkeypatch,
        fixed_now,
        fixed_tokens,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        created = create_session(db)
        db.commit()
        db.expire_all()

        stored_session = db.execute(select(Session)).scalar_one()

        assert stored_session.expires_at.tzinfo is None
        assert get_valid_session(db, created.session_token) is not None
