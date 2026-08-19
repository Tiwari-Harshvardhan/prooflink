from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Instruction(Base):
    __tablename__ = "instructions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    instruction_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    institution_id: Mapped[str] = mapped_column(String(64), ForeignKey("institutions.id"), nullable=False, index=True)
    official_id: Mapped[str] = mapped_column(String(64), ForeignKey("officials.id"), nullable=False, index=True)
    citizen_id: Mapped[str] = mapped_column(String(64), ForeignKey("citizens.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="INR")
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    institution: Mapped["Institution"] = relationship("Institution")
    official: Mapped["Official"] = relationship("Official")
    citizen: Mapped["Citizen"] = relationship("Citizen")
