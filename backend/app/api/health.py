from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=Dict[str, str], summary="Health Check")
def health_check() -> Dict[str, str]:
    """Endpoint 1 — Health Check"""
    return {"status": "healthy"}
