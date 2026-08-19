from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Citizen(Base):
    __tablename__ = "citizens"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    aadhaar_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    aadhaar_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    masked_aadhaar: Mapped[str] = mapped_column(String(32), nullable=False)
    kyc_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    phone_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
