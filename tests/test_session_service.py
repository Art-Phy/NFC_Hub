
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import nfc_hub.core.session_service as service_module
from nfc_hub.core.database import Base
from nfc_hub.core.session_service import (
    CreatedSession,
    create_session,
    delete_expired_sessions,
    delete_session, 
    get_valid_session,
)

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



class TestSessionDeletion:
    def test_deletes_session_using_raw_token(
        self,
        db,
        fixed_tokens,
    ):
        created = create_session(db)
        db.commit()

        deleted = delete_session(db, created.session_token)

        assert deleted is True
        assert get_valid_session(db, created.session_token) is None
        assert db.execute(select(Session)).scalar_one_or_none() is None

    def test_returns_false_for_unknown_token(self, db):
        deleted = delete_session(db, "unknown-session-token")

        assert deleted is False

    def test_does_not_delete_session_for_modified_token(
        self,
        db,
        fixed_tokens,
    ):
        created = create_session(db)
        db.commit()

        deleted = delete_session(
            db,
            f"{created.session_token}-modified",
        )

        assert deleted is False
        assert db.get(Session, created.session.id) is not None

    def test_deletion_can_be_rolled_back(
        self,
        db,
        fixed_tokens,
    ):
        created = create_session(db)
        db.commit()

        delete_session(db, created.session_token)
        db.rollback()

        restored_session = db.get(Session, created.session.id)

        assert restored_session is not None


class TestExpiredSessionCleanup:
    def test_deletes_only_expired_sessions(
        self,
        db,
        monkeypatch,
        fixed_now,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)

        expired_session = Session(
            token_hash=hash_session_token("expired-token"),
            csrf_token="expired-csrf-token",
            expires_at=fixed_now - timedelta(seconds=1),
        )
        valid_session = Session(
            token_hash=hash_session_token("valid-token"),
            csrf_token="valid-csrf-token",
            expires_at=fixed_now + timedelta(seconds=1),
        )
        db.add_all([expired_session, valid_session])
        db.commit()

        deleted_count = delete_expired_sessions(db)

        remaining_sessions = db.execute(select(Session)).scalars().all()

        assert deleted_count == 1
        assert [session.id for session in remaining_sessions] == [
            valid_session.id
        ]



    def test_deletes_session_at_exact_expiration_time(
        self,
        db,
        monkeypatch,
        fixed_now,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        session = Session(
            token_hash=hash_session_token("expired-token"),
            csrf_token="csrf-token",
            expires_at=fixed_now,
        )
        db.add(session)
        db.commit()

        session_id = session.id

        deleted_count = delete_expired_sessions(db)

        stored_session = db.execute(
            select(Session).where(Session.id == session_id)
        ).scalar_one_or_none()

        assert deleted_count == 1
        assert stored_session  is None



    def test_returns_zero_when_no_sessions_are_expired(
        self,
        db,
        monkeypatch,
        fixed_now,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        session = Session(
            token_hash=hash_session_token("valid-token"),
            csrf_token="csrf-token",
            expires_at=fixed_now + timedelta(minutes=15),
        )
        db.add(session)
        db.commit()

        deleted_count = delete_expired_sessions(db)

        assert deleted_count == 0
        assert db.get(Session, session.id) is not None



    def test_cleanup_can_be_rolled_back(
        self,
        db,
        monkeypatch,
        fixed_now,
    ):
        monkeypatch.setattr(service_module, "_utc_now", lambda: fixed_now)
        session = Session(
            token_hash=hash_session_token("expired-token"),
            csrf_token="csrf-token",
            expires_at=fixed_now - timedelta(minutes=1),
        )
        db.add(session)
        db.commit()

        delete_expired_sessions(db)
        db.rollback()

        assert db.get(Session, session.id) is not None
