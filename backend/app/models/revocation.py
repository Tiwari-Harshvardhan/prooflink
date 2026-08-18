from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.prooflink import ProofLink

class Revocation(Base):
    __tablename__ = "revocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proof_id: Mapped[str] = mapped_column(String(64), ForeignKey("prooflinks.proof_id"), unique=True, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    revoked_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    prooflink: Mapped["ProofLink"] = relationship("ProofLink", back_populates="revocation")
