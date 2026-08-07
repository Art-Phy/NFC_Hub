from datetime import datetime

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import nfc_hub.models.user as user_module
from nfc_hub.core.database import Base
from nfc_hub.models import User


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class TestTableDefinition:
    def test_table_name_is_users(self):
        assert User.__tablename__ == "users"

    def test_table_registered_on_base_metadata(self):
        assert "users" in Base.metadata.tables

    def test_columns_and_nullability(self):
        table = User.__table__
        assert set(table.columns.keys()) == {
            "id",
            "email",
            "password_hash",
            "is_active",
            "created_at",
            "updated_at",
        }
        assert table.c.id.primary_key
        assert table.c.email.nullable is False
        assert table.c.password_hash.nullable is False
        assert table.c.is_active.nullable is False
        assert table.c.created_at.nullable is False
        assert table.c.updated_at.nullable is False

    def test_email_unique_index(self):
        unique_index = next(
            index
            for index in User.__table__.indexes
            if index.name == "ix_users_email"
        )
        assert unique_index.unique is True


class TestEmailNormalization:
    def test_email_normalized_on_create(self, db):
        user = User(email="  User@Example.COM ", password_hash="hash")
        db.add(user)
        db.commit()
        assert user.email == "user@example.com"
        db.refresh(user)
        assert user.email == "user@example.com"

    def test_case_variant_duplicate_rejected_through_orm(self, db):
        db.add(User(email="user@example.com", password_hash="hash"))
        db.add(User(email="USER@example.com", password_hash="hash"))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_exact_duplicate_rejected_at_database_level(self, db):
        db.add(User(email="user@example.com", password_hash="hash"))
        db.commit()
        engine = db.get_bind()
        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO users (email, password_hash) "
                        "VALUES (:email, :password_hash)"
                    ),
                    {"email": "user@example.com", "password_hash": "hash"},
                )


class TestRequiredFields:
    def test_missing_email_rejected(self, db):
        db.add(User(password_hash="hash"))
        with pytest.raises(IntegrityError):
            db.commit()

    def test_missing_password_hash_rejected(self, db):
        db.add(User(email="user@example.com"))
        with pytest.raises(IntegrityError):
            db.commit()


class TestActiveDefault:
    def test_is_active_defaults_true_via_orm(self, db):
        user = User(email="user@example.com", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        assert user.is_active is True

    def test_is_active_server_default_on_raw_insert(self, db):
        engine = db.get_bind()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO users (email, password_hash) "
                    "VALUES ('raw@example.com', 'hash')"
                )
            )
        user = db.execute(
            select(User).where(User.email == "raw@example.com")
        ).scalar_one()
        assert user.is_active is True


class TestTimestamps:
    def test_timestamps_populated_on_insert(self, db):
        user = User(email="user@example.com", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_created_at_has_no_onupdate(self):
        assert User.__table__.c.created_at.onupdate is None

    def test_updated_at_has_onupdate(self):
        assert User.__table__.c.updated_at.onupdate is not None

    def test_updated_at_changes_on_update_created_at_stable(self, db, monkeypatch):
        monkeypatch.setattr(
            user_module, "_utc_now", lambda: datetime(2026, 1, 1, 12, 0, 0)
        )
        user = User(email="user@example.com", password_hash="hash")
        db.add(user)
        db.commit()
        assert user.created_at == datetime(2026, 1, 1, 12, 0, 0)
        assert user.updated_at == datetime(2026, 1, 1, 12, 0, 0)

        monkeypatch.setattr(
            user_module, "_utc_now", lambda: datetime(2026, 1, 2, 12, 0, 0)
        )
        user.email = "new@example.com"
        db.commit()
        assert user.created_at == datetime(2026, 1, 1, 12, 0, 0)
        assert user.updated_at == datetime(2026, 1, 2, 12, 0, 0)
