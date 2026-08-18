"""
Demo seed data for PROOFLINK.

Run with:  python seed.py
Populates two institutions and a handful of ProofLinks in ACTIVE,
EXPIRED, and REVOKED states so the frontend has real states to render
against before the backend crypto layer is wired up.

NOTE: The `signature` and `content_hash` values here are placeholders
(clearly marked) — they are NOT real Ed25519 signatures. Real values
must come from the backend/crypto layer.
"""
from datetime import datetime, timedelta, timezone

from database import Base, engine, session_scope
from models import Institution, InstitutionStatus, InstitutionType, ProofLink, ProofLinkStatus, Revocation


def now():
    return datetime.now(timezone.utc)


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with session_scope() as db:
        if db.query(Institution).count() > 0:
            print("Seed data already present — skipping.")
            return

        police = Institution(
            institution_id="INST-POLICE-MH-014",
            name="Maharashtra Police — Cyber Cell",
            type=InstitutionType.POLICE,
            public_key="ed25519:PLACEHOLDER_PUBLIC_KEY_8f3ac21e",
            status=InstitutionStatus.ACTIVE,
        )
        bank = Institution(
            institution_id="INST-BANK-HDFC-001",
            name="HDFC Bank Ltd.",
            type=InstitutionType.BANK,
            public_key="ed25519:PLACEHOLDER_PUBLIC_KEY_2b9177aa",
            status=InstitutionStatus.ACTIVE,
        )
        db.add_all([police, bank])
        db.flush()  # assign institution_id relations are natural keys, but flush for clarity

        active_link = ProofLink(
            proof_id="PL-2026-00123",
            institution_id=police.institution_id,
            action="FUND_TRANSFER",
            amount="80000.00",
            currency="INR",
            recipient="Case Escrow Account #4471",
            purpose="Fraud investigation escrow hold",
            reference_id="FIR-2026-778812",
            issued_at=now() - timedelta(days=1),
            expires_at=now() + timedelta(days=9),
            signature="PLACEHOLDER_SIGNATURE_9f1c4b7e",
            content_hash="PLACEHOLDER_SHA256_71a3e90c",
            status=ProofLinkStatus.ACTIVE,
        )

        expired_link = ProofLink(
            proof_id="PL-2026-00098",
            institution_id=bank.institution_id,
            action="KYC_VERIFICATION_CALL",
            amount="0.00",
            currency="INR",
            recipient="N/A",
            purpose="Scheduled KYC re-verification call",
            reference_id="KYC-REQ-55231",
            issued_at=now() - timedelta(days=21),
            expires_at=now() - timedelta(days=14),
            signature="PLACEHOLDER_SIGNATURE_aa0211d8",
            content_hash="PLACEHOLDER_SHA256_44bb920f",
            status=ProofLinkStatus.EXPIRED,
        )

        revoked_link = ProofLink(
            proof_id="PL-2026-00071",
            institution_id=bank.institution_id,
            action="FUND_TRANSFER",
            amount="150000.00",
            currency="INR",
            recipient="Suspicious External Account",
            purpose="Revoked after internal review",
            reference_id="TXN-REQ-11029",
            issued_at=now() - timedelta(days=34),
            expires_at=now() - timedelta(days=24),
            signature="PLACEHOLDER_SIGNATURE_5c672f01",
            content_hash="PLACEHOLDER_SHA256_0912bbaa",
            status=ProofLinkStatus.REVOKED,
        )

        db.add_all([active_link, expired_link, revoked_link])
        db.flush()

        db.add(
            Revocation(
                proof_id=revoked_link.proof_id,
                reason="Internal review flagged recipient account as suspicious.",
                revoked_at=now() - timedelta(days=20),
                revoked_by="compliance-officer@hdfcbank.example",
            )
        )

        print("Seeded 2 institutions and 3 ProofLinks (ACTIVE, EXPIRED, REVOKED).")


if __name__ == "__main__":
    seed()
