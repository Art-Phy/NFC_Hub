
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from nfc_hub.core.database import Base
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


def future_expiration() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=15)


class TestTableDefinition:
    def test_table_name_is_sessions(self):
        assert Session.__tablename__ == "sessions"

    def test_table_registered_on_base_metadata(self):
        assert "sessions" in Base.metadata.tables

    def test_columns_and_nullability(self):
        table = Session.__table__

        assert set(table.columns.keys()) == {
            "id",
            "token_hash",
            "csrf_token",
            "user_id",
            "created_at",
            "expires_at",
        }
        assert table.c.id.primary_key
        assert table.c.token_hash.nullable is False
        assert table.c.csrf_token.nullable is False
        assert table.c.user_id.nullable is True
        assert table.c.created_at.nullable is False
        assert table.c.expires_at.nullable is False

    def test_token_hash_unique_index(self):
        token_index = next(
            index
            for index in Session.__table__.indexes
            if index.name == "ix_sessions_token_hash"
        )

        assert token_index.unique is True

    def test_user_id_index(self):
        user_index = next(
            index
            for index in Session.__table__.indexes
            if index.name == "ix_sessions_user_id"
        )

        assert user_index.unique is False

    def test_user_foreign_key_uses_cascade_delete(self):
        foreign_key = next(iter(Session.__table__.c.user_id.foreign_keys))

        assert foreign_key.target_fullname == "users.id"
        assert foreign_key.ondelete == "CASCADE"


class TestAnonymousSession:
    def test_session_without_user_is_allowed(self, db):
        session = Session(
            token_hash="a" * 64,
            csrf_token="anonymous-csrf-token",
            expires_at=future_expiration(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        assert session.id is not None
        assert session.user_id is None
        assert session.user is None


class TestAuthenticatedSession:
    def test_session_can_reference_user(self, db):
        user = User(
            email="user@example.com",
            password_hash="password-hash",
        )
        db.add(user)
        db.flush()

        session = Session(
            token_hash="b" * 64,
            csrf_token="authenticated-csrf-token",
            user_id=user.id,
            expires_at=future_expiration(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        assert session.user_id == user.id
        assert session.user == user


class TestRequiredFields:
    def test_missing_token_hash_rejected(self, db):
        db.add(
            Session(
                csrf_token="csrf-token",
                expires_at=future_expiration(),
            )
        )

        with pytest.raises(IntegrityError):
            db.commit()

    def test_missing_csrf_token_rejected(self, db):
        db.add(
            Session(
                token_hash="c" * 64,
                expires_at=future_expiration(),
            )
        )

        with pytest.raises(IntegrityError):
            db.commit()

    def test_missing_expiration_rejected(self, db):
        db.add(
            Session(
                token_hash="d" * 64,
                csrf_token="csrf-token",
            )
        )

        with pytest.raises(IntegrityError):
            db.commit()


class TestTokenUniqueness:
    def test_duplicate_token_hash_rejected(self, db):
        db.add(
            Session(
                token_hash="e" * 64,
                csrf_token="first-csrf-token",
                expires_at=future_expiration(),
            )
        )
        db.commit()

        db.add(
            Session(
                token_hash="e" * 64,
                csrf_token="second-csrf-token",
                expires_at=future_expiration(),
            )
        )

        with pytest.raises(IntegrityError):
            db.commit()


class TestTimestamps:
    def test_created_at_populated_on_insert(self, db):
        session = Session(
            token_hash="f" * 64,
            csrf_token="csrf-token",
            expires_at=future_expiration(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        assert isinstance(session.created_at, datetime)

    def test_created_at_has_no_onupdate(self):
        assert Session.__table__.c.created_at.onupdate is None
