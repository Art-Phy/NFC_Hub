"""Database model for anonymous and authenticated sessions"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nfc_hub.core.database import Base

if TYPE_CHECKING:
    from nfc_hub.models.user import User



def _utc_now() -> datetime:
    return datetime.now(timezone.utc)



class Session(Base):
    __tablename__= "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    csrf_token: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: _utc_now(),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    user: Mapped["User | None"] = relationship()
