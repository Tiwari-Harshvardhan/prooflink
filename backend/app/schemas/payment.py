from datetime import datetime
from pydantic import BaseModel


class PaymentOrderRequest(BaseModel):
    prooflink: str


class PaymentOrderResponse(BaseModel):
    payment_id: str
    amount: float
    currency: str
    status: str
    provider: str


class PaymentVerifyRequest(BaseModel):
    payment_id: str


class PaymentResponse(PaymentOrderResponse):
    paid_at: datetime | None = None
