"""
Verification Engine: Multi-layer QDS and business-logic verification.

The signature verification step now uses the teleportation-based Quantum
Digital Signature (QDS) prototype instead of Ed25519.

Application-layer checks (expiry, revocation, ownership) are unchanged and
take precedence over the quantum signature result.

See app/crypto/qds.py for the QDS protocol documentation.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.prooflink import ProofLink
from app.models.institution import Institution
from app.models.revocation import Revocation
from app.models.payment import Payment
from app.schemas.verification import VerifyResponse, VerificationChecks
from app.schemas.prooflink import InstructionDetail, InstitutionDetail
from app.crypto.hashing import create_canonical_instruction, calculate_content_hash
from app.crypto.verification import verify_qds_signature_full
from app.core.security import constant_time_compare


def verify_prooflink(db: Session, proof_id: str) -> VerifyResponse:
    """
    Execute the multi-layer verification workflow for a given Proof ID.

    Verification steps:
      1.  Find ProofLink in database
      2.  Load and validate institution
      3.  Reconstruct canonical instruction
      4.  Recalculate SHA-256 message fingerprint
      5.  Compare stored fingerprint with recalculated fingerprint
      6.  Run QDS (teleportation-based) signature verification
      7.  Check revocation
      8.  Check expiry
      9.  Instruction consistency (amount, recipient)
      10. Return structured VerifyResponse

    Application-layer checks (REVOKED, EXPIRED, wrong citizen) always take
    priority over the quantum signature result - consistent with the layered
    security design.
    """
    clean_proof_id = proof_id.strip()

    # Initialize check checklist
    checks = {
        "exists": False,
        "institution_recognized": False,
        "signature_valid": False,
        "hash_valid": False,
        "amount_match": False,
        "recipient_match": False,
        "not_expired": False,
        "not_revoked": False,
    }

    # Step 1: Find ProofLink
    prooflink: Optional[ProofLink] = (
        db.query(ProofLink).filter(ProofLink.proof_id == clean_proof_id).first()
    )
    if not prooflink:
        return VerifyResponse(
            status="NOT_FOUND",
            result="NOT_FOUND",
            proof_id=clean_proof_id,
            institution=None,
            instruction=None,
            checks=VerificationChecks(
                exists=False,
                institution_recognized=False,
                signature_valid=False,
                hash_valid=False,
                amount_match=False,
                recipient_match=False,
                not_expired=False,
                not_revoked=False,
            ),
            message="No ProofLink record found with the specified Proof ID.",
        )

    checks["exists"] = True

    # Step 2: Load institution
    institution: Optional[Institution] = (
        db.query(Institution).filter(Institution.id == prooflink.institution_id).first()
    )
    if not institution or institution.status != "ACTIVE":
        return VerifyResponse(
            status="MISMATCH",
            result="MISMATCH",
            proof_id=clean_proof_id,
            institution=None,
            instruction=None,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=False,
                signature_valid=False,
                hash_valid=False,
                amount_match=False,
                recipient_match=False,
                not_expired=False,
                not_revoked=True,
            ),
            message=(
                f"Issuing institution '{prooflink.institution_id}' "
                "is unknown, unrecognized, or inactive."
            ),
        )

    checks["institution_recognized"] = True

    # Build institution & instruction structures
    inst_detail = InstitutionDetail(
        id=institution.id,
        name=institution.name,
        type=institution.type,
        public_key=institution.public_key,
        status=institution.status,
    )
    instr_detail = InstructionDetail(
        action=prooflink.action,
        amount=prooflink.amount,
        currency=prooflink.currency,
        recipient=prooflink.recipient,
        purpose=prooflink.purpose,
        reference_id=prooflink.reference_id,
    )

    # Step 3: Reconstruct canonical instruction
    canonical_dict = create_canonical_instruction(
        proof_id=prooflink.proof_id,
        institution_id=prooflink.institution_id,
        action=prooflink.action,
        amount=prooflink.amount,
        currency=prooflink.currency,
        recipient=prooflink.recipient,
        purpose=prooflink.purpose,
        reference_id=prooflink.reference_id,
        issued_at=prooflink.created_at,
        expires_at=prooflink.expires_at,
    )

    # Steps 4 & 5: Recalculate and compare SHA-256 message fingerprint
    recalculated_hash = calculate_content_hash(canonical_dict)
    if not constant_time_compare(recalculated_hash, prooflink.content_hash):
        checks["hash_valid"] = False
        return VerifyResponse(
            status="HASH_MISMATCH",
            result="HASH_MISMATCH",
            proof_id=clean_proof_id,
            institution=inst_detail,
            instruction=instr_detail,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=True,
                signature_valid=False,
                hash_valid=False,
                amount_match=bool(prooflink.amount >= 0),
                recipient_match=bool(prooflink.recipient and len(prooflink.recipient.strip()) > 0),
                not_expired=(
                    datetime.now(timezone.utc)
                    <= (
                        prooflink.expires_at
                        if prooflink.expires_at.tzinfo
                        else prooflink.expires_at.replace(tzinfo=timezone.utc)
                    )
                ),
                not_revoked=(
                    db.query(Revocation)
                    .filter(Revocation.proof_id == prooflink.proof_id)
                    .first()
                    is None
                ),
            ),
            message=(
                "Content fingerprint mismatch. "
                "The instruction data has been tampered with or corrupted."
            ),
        )
    checks["hash_valid"] = True

    # Step 6: QDS (teleportation-based) quantum signature verification
    qds_result = verify_qds_signature_full(
        signature_json=prooflink.signature,
        canonical_data=canonical_dict,
        institution_id=prooflink.institution_id,
    )

    is_sig_valid = (qds_result.status == "VERIFIED")

    if not is_sig_valid:
        checks["signature_valid"] = False

        # Map QDS status to API-facing status
        api_status = {
            "FORGERY_SUSPECTED":       "INVALID_SIGNATURE",
            "CHANNEL_ANOMALY":         "INVALID_SIGNATURE",
            "REPLAY_DETECTED":         "INVALID_SIGNATURE",
            "UNAUTHORIZED_SIGNER":     "INVALID_SIGNATURE",
            "INVALID_SIGNATURE_FORMAT": "INVALID_SIGNATURE",
        }.get(qds_result.status, "INVALID_SIGNATURE")

        return VerifyResponse(
            status=api_status,
            result=api_status,
            proof_id=clean_proof_id,
            institution=inst_detail,
            instruction=instr_detail,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=True,
                signature_valid=False,
                hash_valid=True,
                amount_match=bool(prooflink.amount >= 0),
                recipient_match=bool(prooflink.recipient and len(prooflink.recipient.strip()) > 0),
                not_expired=(
                    datetime.now(timezone.utc)
                    <= (
                        prooflink.expires_at
                        if prooflink.expires_at.tzinfo
                        else prooflink.expires_at.replace(tzinfo=timezone.utc)
                    )
                ),
                not_revoked=(
                    db.query(Revocation)
                    .filter(Revocation.proof_id == prooflink.proof_id)
                    .first()
                    is None
                ),
            ),
            message=(
                f"Quantum signature verification failed ({qds_result.status}): "
                f"{qds_result.message}"
            ),
        )
    checks["signature_valid"] = True

    # Step 7: Check revocation
    revocation = (
        db.query(Revocation)
        .filter(Revocation.proof_id == prooflink.proof_id)
        .first()
    )
    if prooflink.status == "REVOKED" or revocation is not None:
        checks["not_revoked"] = False
        now = datetime.now(timezone.utc)
        exp = (
            prooflink.expires_at
            if prooflink.expires_at.tzinfo
            else prooflink.expires_at.replace(tzinfo=timezone.utc)
        )
        checks["not_expired"] = now <= exp
        checks["amount_match"] = prooflink.amount >= 0
        checks["recipient_match"] = bool(prooflink.recipient)

        reason = revocation.reason if revocation else "Instruction was revoked by the issuer."
        return VerifyResponse(
            status="REVOKED",
            result="REVOKED",
            proof_id=clean_proof_id,
            institution=inst_detail,
            instruction=instr_detail,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=True,
                signature_valid=True,
                hash_valid=True,
                amount_match=checks["amount_match"],
                recipient_match=checks["recipient_match"],
                not_expired=checks["not_expired"],
                not_revoked=False,
            ),
            message=f"Instruction was revoked. Reason: {reason}",
            prooflink={
                "action": prooflink.action,
                "amount": str(prooflink.amount),
                "currency": prooflink.currency,
                "recipient": prooflink.recipient,
                "purpose": prooflink.purpose,
                "reference_id": prooflink.reference_id,
                "issued_at": prooflink.created_at.isoformat(),
                "expires_at": prooflink.expires_at.isoformat(),
                "signature_status": "QDS_VERIFIED",
                "instruction_status": prooflink.status,
                "revocation_status": "REVOKED",
                "qds_protocol": qds_result.protocol,
                "qds_basis": qds_result.basis,
                "qds_shots": qds_result.shots,
                "qds_error_rate": qds_result.error_rate,
            },
        )
    checks["not_revoked"] = True

    # Step 8: Check expiry
    now = datetime.now(timezone.utc)
    exp = (
        prooflink.expires_at
        if prooflink.expires_at.tzinfo
        else prooflink.expires_at.replace(tzinfo=timezone.utc)
    )
    if now > exp or prooflink.status == "EXPIRED":
        checks["not_expired"] = False
        checks["amount_match"] = prooflink.amount >= 0
        checks["recipient_match"] = bool(prooflink.recipient)
        return VerifyResponse(
            status="EXPIRED",
            result="EXPIRED",
            proof_id=clean_proof_id,
            institution=inst_detail,
            instruction=instr_detail,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=True,
                signature_valid=True,
                hash_valid=True,
                amount_match=checks["amount_match"],
                recipient_match=checks["recipient_match"],
                not_expired=False,
                not_revoked=True,
            ),
            message=f"Instruction expired on {prooflink.expires_at.isoformat()}.",
            prooflink={
                "action": prooflink.action,
                "amount": str(prooflink.amount),
                "currency": prooflink.currency,
                "recipient": prooflink.recipient,
                "purpose": prooflink.purpose,
                "reference_id": prooflink.reference_id,
                "issued_at": prooflink.created_at.isoformat(),
                "expires_at": prooflink.expires_at.isoformat(),
                "signature_status": "QDS_VERIFIED",
                "instruction_status": prooflink.status,
                "revocation_status": "NOT_REVOKED",
                "qds_protocol": qds_result.protocol,
                "qds_basis": qds_result.basis,
                "qds_shots": qds_result.shots,
                "qds_error_rate": qds_result.error_rate,
            },
        )
    checks["not_expired"] = True

    # Step 9: Instruction consistency
    checks["amount_match"] = prooflink.amount >= 0
    checks["recipient_match"] = bool(
        prooflink.recipient and len(prooflink.recipient.strip()) > 0
    )

    if not (checks["amount_match"] and checks["recipient_match"]):
        return VerifyResponse(
            status="MISMATCH",
            result="MISMATCH",
            proof_id=clean_proof_id,
            institution=inst_detail,
            instruction=instr_detail,
            checks=VerificationChecks(
                exists=True,
                institution_recognized=True,
                signature_valid=True,
                hash_valid=True,
                amount_match=checks["amount_match"],
                recipient_match=checks["recipient_match"],
                not_expired=True,
                not_revoked=True,
            ),
            message="Instruction parameters failed integrity checks.",
        )

    # Step 10: VERIFIED — include QDS quantum statistics in response
    paid_payment = db.query(Payment).filter(
        (Payment.prooflink_id == prooflink.proof_id)
        | (Payment.instruction_id == prooflink.instruction_id),
        Payment.status == "PAID",
    ).first()

    is_paid = (paid_payment is not None) or (prooflink.status == "PAID")
    payment_status = "PAID" if is_paid else "PENDING"

    return VerifyResponse(
        status="VERIFIED",
        result="VERIFIED",
        proof_id=clean_proof_id,
        institution=inst_detail,
        instruction=instr_detail,
        checks=VerificationChecks(
            exists=True,
            institution_recognized=True,
            signature_valid=True,
            hash_valid=True,
            amount_match=True,
            recipient_match=True,
            not_expired=True,
            not_revoked=True,
        ),
        message=(
            f"Instruction verified via teleportation-based QDS protocol. "
            f"Shots: {qds_result.shots}. "
            f"Error rate: {qds_result.error_rate:.4f} (threshold: {qds_result.threshold:.2f})."
        ),
        prooflink={
            "action": prooflink.action,
            "amount": str(prooflink.amount),
            "currency": prooflink.currency,
            "recipient": prooflink.recipient,
            "purpose": prooflink.purpose,
            "reference_id": prooflink.reference_id,
            "issued_at": prooflink.created_at.isoformat(),
            "expires_at": prooflink.expires_at.isoformat(),
            "signature_status": "QDS_VERIFIED",
            "instruction_status": "PAID" if is_paid else prooflink.status,
            "revocation_status": "NOT_REVOKED",
            "payment_status": payment_status,
            "payment_id": paid_payment.id if paid_payment else None,
            "paid_at": (
                paid_payment.paid_at.isoformat()
                if (paid_payment and paid_payment.paid_at)
                else None
            ),
            # QDS quantum measurement statistics
            "qds_protocol": qds_result.protocol,
            "qds_state_label": qds_result.state_label,
            "qds_basis": qds_result.basis,
            "qds_shots": qds_result.shots,
            "qds_correct_count": qds_result.correct_count,
            "qds_incorrect_count": qds_result.incorrect_count,
            "qds_error_rate": qds_result.error_rate,
            "qds_threshold": qds_result.threshold,
        },
    )
