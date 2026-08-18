from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.prooflink import ProofLink

class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # POLICE, BANK, GOVERNMENT, etc.
    public_key: Mapped[str] = mapped_column(String(255), nullable=False)  # Base64 encoded Ed25519 public key
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    prooflinks: Mapped[List["ProofLink"]] = relationship(
        "ProofLink", back_populates="institution", cascade="all, delete-orphan"
    )
