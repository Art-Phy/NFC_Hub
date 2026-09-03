
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock

import nfc_hub.core.auth_service as service_module
from nfc_hub.core.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
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



class TestUserAuthentication:
    def test_authenticates_user_with_normalized_email(
        self,
        db,
        monkeypatch,
    ):
        user = User(
            email="user@example.com",
            password_hash="stored-password-hash",
        )
        db.add(user)
        db.commit()

        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: True,
        )
        monkeypatch.setattr(
            service_module,
            "password_needs_rehash",
            lambda password_hash: False,
        )

        authenticated_user = authenticate_user(
            db,
            email="  USER@EXAMPLE.COM  ",
            password="correct-password",
        )

        assert authenticated_user.id == user.id
        assert authenticated_user.email == "user@example.com"


    def test_rejects_incorrect_password(
        self,
        db,
        monkeypatch,
    ):
        user = User(
            email="user@example.com",
            password_hash="stored-password-hash",
        )
        db.add(user)
        db.commit()

        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: False,
        )

        with pytest.raises(
            InvalidCredentialsError,
            match="Invalid email or password",
        ):
            authenticate_user(
                db,
                email="user@example.com",
                password="incorrect-password",
            )


    def test_rejects_unknown_email_with_same_error(
        self,
        db,
        monkeypatch,
    ):
        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: False,
        )

        with pytest.raises(
            InvalidCredentialsError,
            match="Invalid email or password",
        ):
            authenticate_user(
                db,
                email="unknown@example.com",
                password="some-password",
            )


    def test_verifies_dummy_hash_for_unknown_email(
        self,
        db,
        monkeypatch,
    ):
        received_arguments = []


        def fake_verify_password(password, password_hash):
            received_arguments.append((password, password_hash))
            return False

        monkeypatch.setattr(
            service_module,
            "verify_password",
            fake_verify_password,
        )

        with pytest.raises(InvalidCredentialsError):
            authenticate_user(
                db,
                email="unknown@example.com",
                password="some-password",
            )

        assert len(received_arguments) == 1
        assert received_arguments[0][0] == "some-password"
        assert received_arguments[0][1] == service_module._DUMMY_PASSWORD_HASH


    def test_rejects_inactive_user_with_same_error(
        self,
        db,
        monkeypatch,
    ):
        user = User(
            email="user@example.com",
            password_hash="stored-password-hash",
            is_active=False,
        )
        db.add(user)
        db.commit()

        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: True,
        )

        with pytest.raises(
            InvalidCredentialsError,
            match="Invalid email or password",
        ):
            authenticate_user(
                db,
                email="user@example.com",
                password="correct-password",
            )

    def test_rehashes_password_when_parameters_are_outdated(
        self,
        db,
        monkeypatch,
    ):
        user = User(
            email="user@example.com",
            password_hash="outdated-password-hash",
        )
        db.add(user)
        db.commit()

        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: True,
        )
        monkeypatch.setattr(
            service_module,
            "password_needs_rehash",
            lambda password_hash: True,
        )
        monkeypatch.setattr(
            service_module,
            "hash_password",
            lambda password: "updated-password-hash",
        )

        authenticated_user = authenticate_user(
            db,
            email="user@example.com",
            password="correct-password",
        )

        assert authenticated_user.password_hash == "updated-password-hash"

    def test_keeps_current_password_hash(
        self,
        db,
        monkeypatch,
    ):
        user = User(
            email="user@example.com",
            password_hash="current-password-hash",
        )
        db.add(user)
        db.commit()

        monkeypatch.setattr(
            service_module,
            "verify_password",
            lambda password, password_hash: True,
        )
        monkeypatch.setattr(
            service_module,
            "password_needs_rehash",
            lambda password_hash: False,
        )

        hash_mock = Mock()
        monkeypatch.setattr(
            service_module,
            "hash_password",
            hash_mock,
        )

        authenticated_user = authenticate_user(
            db,
            email="user@example.com",
            password="correct-password",
        )

        assert authenticated_user.password_hash == "current-password-hash"
        hash_mock.assert_not_called()
