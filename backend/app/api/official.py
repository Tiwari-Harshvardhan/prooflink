from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.connection import get_db
from app.schemas.instruction import CreateInstructionRequest, CreateInstructionResponse
from app.services.auth_service import get_official_by_user_id
from app.services.instruction_service import create_instruction_for_official

router = APIRouter(prefix="/official", tags=["Official"])


@router.post("/instructions", response_model=CreateInstructionResponse, status_code=status.HTTP_201_CREATED)
def create_instruction(payload: CreateInstructionRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "OFFICIAL":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only officials can create instructions.")
    official = get_official_by_user_id(db, current_user.id)
    if not official:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Official profile not found.")
    instruction, notification = create_instruction_for_official(db, official, payload)
    return CreateInstructionResponse(
        instruction_id=instruction.instruction_id, status="CREATED",
        notification_status=notification.get("status", "QUEUED").upper(),
        message="Instruction created. The ProofLink was delivered only to the citizen's verified phone number.",
    )
