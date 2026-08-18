from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.revocation import Revocation

class ProofLink(Base):
    __tablename__ = "prooflinks"

    proof_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(64), ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Instruction data
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., PAYMENT, FREEZE, COURT_SUMMONS
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="INR")
    recipient: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    
    # Cryptographic integrity & authorization
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hex
    signature: Mapped[str] = mapped_column(Text, nullable=False)  # Ed25519 signature in Base64
    
    # Lifecycle & status
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, REVOKED, EXPIRED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="prooflinks")
    revocation: Mapped[Optional["Revocation"]] = relationship("Revocation", back_populates="prooflink", uselist=False, cascade="all, delete-orphan")
