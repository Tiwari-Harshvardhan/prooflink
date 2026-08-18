"""
SQLAlchemy models for the PROOFLINK registry.

Ownership note (see project spec): this file defines schema only.
- No Ed25519 / signing logic lives here.
- No private key column exists anywhere in this schema — `institutions.public_key`
  stores the institution's PUBLIC key only. Private keys belong to the
  cryptographic/backend layer and must never be persisted alongside this data.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InstitutionType(str, enum.Enum):
    POLICE = "POLICE"
    BANK = "BANK"
    GOVERNMENT = "GOVERNMENT"
    COURT = "COURT"
    TELECOM = "TELECOM"
    OTHER = "OTHER"


class InstitutionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class ProofLinkStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class Institution(Base):
    """An authority (police department, bank, government office, ...)
    that can issue signed instructions."""

    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Public-facing, human-referenceable identifier, e.g. "INST-POLICE-MH-014".
    institution_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[InstitutionType] = mapped_column(Enum(InstitutionType, name="institution_type"), nullable=False)

    # PUBLIC key only. Never store a private key in this table or any other.
    public_key: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[InstitutionStatus] = mapped_column(
        Enum(InstitutionStatus, name="institution_status"),
        nullable=False,
        default=InstitutionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    prooflinks: Mapped[list["ProofLink"]] = relationship(back_populates="institution")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Institution {self.institution_id} {self.name!r}>"


class ProofLink(Base):
    """A single signed instruction that a citizen can independently verify."""

    __tablename__ = "prooflinks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Public-facing identifier shared with the citizen, e.g. "PL-2026-00123".
    proof_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False, default=lambda: _generate_proof_id()
    )

    institution_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("institutions.institution_id"), nullable=False, index=True
    )

    action: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[str] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    reference_id: Mapped[str] = mapped_column(String(128), nullable=False)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Produced by the crypto/backend layer. The frontend never computes these.
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    status: Mapped[ProofLinkStatus] = mapped_column(
        Enum(ProofLinkStatus, name="prooflink_status"),
        nullable=False,
        default=ProofLinkStatus.ACTIVE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    institution: Mapped["Institution"] = relationship(back_populates="prooflinks")
    revocation: Mapped["Revocation | None"] = relationship(back_populates="prooflink", uselist=False)

    __table_args__ = (
        Index("ix_prooflinks_institution_status", "institution_id", "status"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ProofLink {self.proof_id} status={self.status}>"


class Revocation(Base):
    """A record of why and when a ProofLink was revoked."""

    __tablename__ = "revocations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    proof_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("prooflinks.proof_id"), unique=True, nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    revoked_by: Mapped[str] = mapped_column(String(255), nullable=False)

    prooflink: Mapped["ProofLink"] = relationship(back_populates="revocation")

    __table_args__ = (UniqueConstraint("proof_id", name="uq_revocations_proof_id"),)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Revocation {self.proof_id} by={self.revoked_by!r}>"


def _generate_proof_id() -> str:
    """Fallback ID generator for scripts/tests. The real backend's
    creation endpoint is expected to assign proof_id explicitly."""
    year = datetime.now(timezone.utc).year
    return f"PL-{year}-{str(uuid.uuid4().int)[:5]}"
