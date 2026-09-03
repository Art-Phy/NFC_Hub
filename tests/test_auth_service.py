
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import nfc_hub.core.auth_service as service_module
from nfc_hub.core.auth_service import (
    EmailAlreadyRegisteredError,
    register_user,
)
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
    database_session = session_factory()

    try:
        yield database_session
    finally:
        database_session.close()
        engine.dispose()



class TestUserRegistration:
    def test_creates_active_user(self, db, monkeypatch):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )

        user = register_user(
            db,
            email="user@example.com",
            password="secure-password",
        )

        assert user.id is not None
        assert user.email == "user@example.com"
        assert user.password_hash == "generated-password-hash"
        assert user.is_active is True



    def test_normalizes_email(self, db, monkeypatch):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )

        user = register_user(
            db,
            email="  User@Example.COM  ",
            password="secure-password",
        )

        assert user.email == "user@example.com"



    def test_hashes_password_before_storage(self, db, monkeypatch):
        received_passwords = []

        def fake_hash_password(password):
            received_passwords.append(password)
            return "generated-password-hash"

        monkeypatch.setattr(
            service_module,
            "hash_password",
            fake_hash_password,
        )

        user = register_user(
            db,
            email="user@example.com",
            password="plain-text-password",
        )

        assert received_passwords == ["plain-text-password"]
        assert user.password_hash == "generated-password-hash"
        assert user.password_hash != "plain-text-password"



    def test_user_is_available_in_current_transaction(
        self,
        db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )

        created_user = register_user(
            db,
            email="user@example.com",
            password="secure-password",
        )

        stored_user = db.execute(
            select(User).where(User.id == created_user.id)
        ).scalar_one()

        assert stored_user is created_user



    def test_rejects_registered_email(self, db, monkeypatch):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )
        register_user(
            db,
            email="user@example.com",
            password="first-password",
        )

        with pytest.raises(
            EmailAlreadyRegisteredError,
            match="Email address is already registered",
        ):
            register_user(
                db,
                email="user@example.com",
                password="second-password",
            )

        users = db.execute(select(User)).scalars().all()

        assert len(users) == 1



    def test_rejects_case_and_whitespace_variant(
        self,
        db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )
        register_user(
            db,
            email="user@example.com",
            password="first-password",
        )

        with pytest.raises(EmailAlreadyRegisteredError):
            register_user(
                db,
                email="  USER@EXAMPLE.COM  ",
                password="second-password",
            )



    def test_registration_can_be_rolled_back(
        self,
        db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "generated-password-hash",
        )

        register_user(
            db,
            email="user@example.com",
            password="secure-password",
        )
        db.rollback()

        stored_user = db.execute(
            select(User).where(User.email == "user@example.com")
        ).scalar_one_or_none()

        assert stored_user is None
