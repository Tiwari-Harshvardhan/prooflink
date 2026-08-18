from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.prooflinks import router as prooflinks_router
from app.api.verification import router as verification_router
from app.api.institutions import router as institutions_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(prooflinks_router)
api_router.include_router(verification_router)
api_router.include_router(institutions_router)

__all__ = ["api_router"]
