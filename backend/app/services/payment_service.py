from datetime import datetime, timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.prooflink import ProofLink
from app.models.instruction import Instruction


def create_mock_payment_order(db: Session, citizen_id: str, proof_id: str) -> Payment:
    prooflink = db.query(ProofLink).filter(ProofLink.proof_id == proof_id, ProofLink.citizen_id == citizen_id).first()
    if not prooflink:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This ProofLink is not available for payment by your verified identity.")
    if prooflink.status == "REVOKED" or prooflink.status == "EXPIRED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This ProofLink is no longer active.")
    existing = db.query(Payment).filter(Payment.prooflink_id == proof_id, Payment.status == "PAID").first()
    if existing or prooflink.status == "PAID":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This instruction has already been paid.")
    payment = Payment(
        id=f"PAY-{uuid.uuid4().hex[:12].upper()}",
        instruction_id=prooflink.instruction_id,
        prooflink_id=prooflink.proof_id,
        citizen_id=citizen_id,
        amount=prooflink.amount,
        payment_provider="MOCK",
        provider_payment_id=f"MOCK-{uuid.uuid4().hex[:12].upper()}",
        status="PENDING",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_mock_payment(db: Session, citizen_id: str, payment_id: str) -> Payment:
    payment = db.query(Payment).filter(Payment.id == payment_id, Payment.citizen_id == citizen_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    if payment.status != "PAID":
        payment.status = "PAID"
        payment.paid_at = datetime.now(timezone.utc)
        instruction = db.query(Instruction).filter(Instruction.instruction_id == payment.instruction_id).first()
        if instruction:
            instruction.status = "PAID"
        prooflink = db.query(ProofLink).filter(ProofLink.proof_id == payment.prooflink_id).first()
        if prooflink:
            prooflink.status = "PAID"
        db.commit()
        db.refresh(payment)
    return payment
