import threading
from pathlib import Path

from alembic.config import Config
from alembic import command
from sqlalchemy import text

from nfc_hub.core.database import Base, SessionLocal, build_engine, engine

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent


class TestBuildEngine:
    def test_returns_sqlite_engine_by_default(self):
        eng = build_engine()
        assert eng.name == "sqlite"

    def test_accepts_custom_url(self):
        eng = build_engine("sqlite:///:memory:")
        assert eng.name == "sqlite"

    def test_can_connect_to_in_memory(self):
        eng = build_engine("sqlite:///:memory:")
        with eng.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1


class TestSessionLocal:
    def test_bound_to_application_engine(self):
        db = SessionLocal()
        try:
            assert db.get_bind() is engine
        finally:
            db.close()


class TestSQLiteThreadSafety:
    def test_connections_work_across_threads(self, tmp_path):
        db_file = tmp_path / "test_threads.db"
        database_url = f"sqlite:///{db_file}"
        eng = build_engine(database_url)

        with eng.begin() as conn:
            conn.execute(text("CREATE TABLE test_threads (id INTEGER)"))
            conn.execute(text("INSERT INTO test_threads VALUES (42)"))

        results = []

        def read_from_worker():
            with eng.connect() as conn:
                results.append(
                    conn.execute(text("SELECT id FROM test_threads")).scalar()
                )

        worker = threading.Thread(target=read_from_worker)
        worker.start()
        worker.join()

        assert results == [42]
        eng.dispose()


class TestDeclarativeBase:
    def test_base_has_metadata(self):
        assert hasattr(Base, "metadata")

    def test_base_registry_is_available(self):
        assert hasattr(Base, "registry")


class TestAlembicConfig:
    def test_check_without_migrations(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_DATABASE_URL", "sqlite:///:memory:")
        cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.check(cfg)

    def test_current_without_migrations(self, monkeypatch):
        monkeypatch.setenv("NFC_HUB_DATABASE_URL", "sqlite:///:memory:")
        cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
        command.current(cfg)
