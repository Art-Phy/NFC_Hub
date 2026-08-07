from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent


@pytest.fixture()
def alembic_config(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration_test.db'}"
    monkeypatch.setenv("NFC_HUB_DATABASE_URL", database_url)
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    return config, database_url


class TestUpgrade:
    def test_creates_users_table(self, alembic_config):
        config, database_url = alembic_config
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            inspector = inspect(engine)
            assert "users" in inspector.get_table_names()
            columns = {
                column["name"]: column
                for column in inspector.get_columns("users")
            }
            assert set(columns) == {
                "id",
                "email",
                "password_hash",
                "is_active",
                "created_at",
                "updated_at",
            }
            assert columns["email"]["nullable"] is False
            assert columns["password_hash"]["nullable"] is False
            indexes = {
                index["name"]: index
                for index in inspector.get_indexes("users")
            }
            assert "ix_users_email" in indexes
            assert indexes["ix_users_email"]["unique"]
        finally:
            engine.dispose()

    def test_insert_uses_database_defaults_and_rejects_exact_duplicate(
        self, alembic_config
    ):
        config, database_url = alembic_config
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO users (email, password_hash) "
                        "VALUES (:email, :password_hash)"
                    ),
                    {"email": "user@example.com", "password_hash": "hash"},
                )
            with engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT is_active, created_at, updated_at "
                        "FROM users"
                    )
                ).one()
            assert row.is_active == 1
            assert row.created_at is not None
            assert row.updated_at is not None

            with pytest.raises(IntegrityError):
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "INSERT INTO users (email, password_hash) "
                            "VALUES (:email, :password_hash)"
                        ),
                        {"email": "user@example.com", "password_hash": "hash"},
                    )
        finally:
            engine.dispose()


class TestDowngrade:
    def test_downgrade_removes_users_table_and_reaches_base(
        self, alembic_config
    ):
        config, database_url = alembic_config
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        engine = create_engine(database_url)
        try:
            assert "users" not in inspect(engine).get_table_names()
            with engine.connect() as conn:
                context = MigrationContext.configure(conn)
                assert context.get_current_revision() is None
        finally:
            engine.dispose()

    def test_reversible_in_both_directions(self, alembic_config):
        config, database_url = alembic_config
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            assert "users" in inspect(engine).get_table_names()
        finally:
            engine.dispose()


class TestAutogenerateConsistency:
    def test_check_reports_no_pending_changes(self, alembic_config):
        config, _database_url = alembic_config
        command.upgrade(config, "head")
        command.check(config)
