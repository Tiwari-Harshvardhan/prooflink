from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    instruction_id: Mapped[str] = mapped_column(String(128), ForeignKey("instructions.instruction_id"), nullable=False, index=True)
    prooflink_id: Mapped[str] = mapped_column(String(128), ForeignKey("prooflinks.proof_id"), nullable=False, index=True)
    citizen_id: Mapped[str] = mapped_column(String(64), ForeignKey("citizens.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payment_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="MOCK")
    provider_payment_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    prooflink: Mapped["ProofLink"] = relationship("ProofLink")
    citizen: Mapped["Citizen"] = relationship("Citizen")
