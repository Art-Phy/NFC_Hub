from sqlalchemy import Engine, create_engine as _create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from nfc_hub.core.settings import get_settings


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return _create_engine(url, connect_args=connect_args)


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
