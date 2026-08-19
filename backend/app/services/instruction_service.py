"""Authoritative official instruction workflow."""
from datetime import timezone
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.instruction import Instruction
from app.models.user import User
from app.schemas.instruction import CreateInstructionRequest
from app.schemas.prooflink import CreateProofLinkRequest
from app.services.auth_service import aadhaar_hash, normalize_phone
from app.services.prooflink_service import create_prooflink
from app.services.sms.sms_service import get_sms_service


def create_instruction_for_official(db: Session, official, request: CreateInstructionRequest) -> tuple[Instruction, dict]:
    phone = normalize_phone(request.citizen_phone)
    citizen = db.query(Citizen).join(User).filter(
        Citizen.aadhaar_hash == aadhaar_hash(request.citizen_aadhaar_number),
        User.phone == phone,
        Citizen.kyc_status == "VERIFIED",
        Citizen.phone_verified.is_(True),
    ).first()
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Citizen verification failed. The provided identity and mobile number do not correspond to a verified citizen.",
        )
    if db.query(Instruction).filter(Instruction.instruction_id == request.instruction_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An instruction with this instruction ID already exists.")

    issued_at = request.issued_at if request.issued_at.tzinfo else request.issued_at.replace(tzinfo=timezone.utc)
    due_at = request.due_at if request.due_at.tzinfo else request.due_at.replace(tzinfo=timezone.utc)
    if due_at <= issued_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Due date must be after issue date.")

    instruction = Instruction(
        id=f"INSTRUCTION-{uuid.uuid4().hex[:12].upper()}",
        instruction_id=request.instruction_id,
        institution_id=official.institution_id,
        official_id=official.id,
        citizen_id=citizen.id,
        action=request.action.upper(), amount=request.amount, currency=request.currency.upper(),
        purpose=request.purpose, reference_id=request.reference_id,
        issued_at=issued_at, due_at=due_at, status="ACTIVE",
    )
    db.add(instruction)
    db.flush()

    citizen_user = citizen.user
    prooflink = create_prooflink(
        db,
        CreateProofLinkRequest(
            institution_id=official.institution_id, action=request.action, amount=request.amount,
            currency=request.currency, recipient=citizen_user.name, purpose=request.purpose,
            reference_id=request.reference_id, instruction_id=request.instruction_id,
            aadhaar_number=request.citizen_aadhaar_number, phone_number=phone, expires_at=due_at,
        ),
        citizen_id=citizen.id, official_id=official.id,
    )
    sms_message = (
        "PROOFLINK: A new official instruction has been issued for your account.\n\n"
        f"Instruction ID: {request.instruction_id}\nAmount: {request.currency.upper()} {request.amount:,.2f}\n"
        f"Due Date: {due_at.strftime('%d %b %Y')}\n\n"
        f"Verify securely: {__import__('app.core.config', fromlist=['settings']).settings.FRONTEND_URL}/verify?token={prooflink.proof_id}"
    )
    try:
        notification = get_sms_service().send_sms(phone, sms_message)
    except Exception:
        # Preserve the instruction as created but surface an accurate delivery
        # state instead of claiming a message was delivered.
        notification = {"status": "FAILED"}
    return instruction, notification
