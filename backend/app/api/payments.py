from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database.connection import get_db
from app.schemas.payment import PaymentOrderRequest, PaymentOrderResponse, PaymentVerifyRequest, PaymentResponse
from app.services.auth_service import get_citizen_by_user_id
from app.services.payment_service import create_mock_payment_order, confirm_mock_payment

router = APIRouter(prefix="/payments", tags=["Payments"])


def citizen_for(current_user, db):
    if current_user.role != "CITIZEN": raise HTTPException(status_code=403, detail="Only citizens can make payments.")
    citizen = get_citizen_by_user_id(db, current_user.id)
    if not citizen or not citizen.phone_verified: raise HTTPException(status_code=403, detail="Verified citizen identity required.")
    return citizen


@router.post("/create-order", response_model=PaymentOrderResponse)
def create_order(payload: PaymentOrderRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    payment = create_mock_payment_order(db, citizen_for(current_user, db).id, payload.prooflink)
    return PaymentOrderResponse(payment_id=payment.id, amount=payment.amount, currency="INR", status=payment.status, provider=payment.payment_provider)


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(payload: PaymentVerifyRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    payment = confirm_mock_payment(db, citizen_for(current_user, db).id, payload.payment_id)
    return PaymentResponse(payment_id=payment.id, amount=payment.amount, currency="INR", status=payment.status, provider=payment.payment_provider, paid_at=payment.paid_at)
