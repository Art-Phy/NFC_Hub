from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, validates

from nfc_hub.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: _utc_now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: _utc_now(),
        onupdate=lambda: _utc_now(),
        server_default=func.now(),
    )

    @validates("email")
    def _normalize_email(self, _key: str, email: object) -> object:
        if email is None:
            return None
        return str(email).strip().lower()
