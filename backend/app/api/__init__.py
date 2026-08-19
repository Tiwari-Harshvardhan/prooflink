from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.prooflinks import router as prooflinks_router
from app.api.verification import router as verification_router
from app.api.institutions import router as institutions_router
from app.api.official import router as official_router
from app.api.payments import router as payments_router
from app.api.dev import router as dev_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(prooflinks_router)
api_router.include_router(verification_router)
api_router.include_router(institutions_router)
api_router.include_router(official_router)
api_router.include_router(payments_router)
api_router.include_router(dev_router)

__all__ = ["api_router"]
