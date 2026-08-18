from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class InstitutionBase(BaseModel):
    name: str = Field(..., example="Madhya Pradesh Police Department")
    type: str = Field(..., example="POLICE")
    status: str = Field(default="ACTIVE", example="ACTIVE")

class InstitutionCreate(InstitutionBase):
    institution_id: str = Field(..., example="POLICE-MP-001")
    public_key: Optional[str] = Field(None, description="Base64 encoded Ed25519 public key. If omitted, will be auto-generated.")

class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    institution_id: str = Field(..., alias="institution_id", example="POLICE-MP-001")
    name: str = Field(..., example="Madhya Pradesh Police Department")
    type: str = Field(..., example="POLICE")
    public_key: str = Field(..., example="Base64PublicKeyString...")
    status: str = Field(..., example="ACTIVE")

    @classmethod
    def from_orm_model(cls, inst):
        return cls(
            institution_id=inst.id,
            name=inst.name,
            type=inst.type,
            public_key=inst.public_key,
            status=inst.status
        )
