from datetime import datetime
from pydantic import BaseModel, Field


class CreateInstructionRequest(BaseModel):
    citizen_aadhaar_number: str = Field(..., min_length=12)
    citizen_phone: str = Field(..., min_length=8)
    instruction_id: str = Field(..., min_length=1, max_length=128)
    action: str
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    purpose: str
    reference_id: str
    issued_at: datetime
    due_at: datetime


class CreateInstructionResponse(BaseModel):
    instruction_id: str
    status: str
    notification_status: str
    message: str
