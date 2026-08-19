"""
Developer-only endpoints for local demo purposes.
These routes are only mounted when ENVIRONMENT=development.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.core.config import settings
from app.services.sms.sms_service import MockSMSProvider

router = APIRouter(prefix="/dev", tags=["Dev (Demo Only)"])


def _require_dev():
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This endpoint is only available in development mode."
        )


@router.get(
    "/sms-inbox",
    summary="[DEMO] Mock SMS Inbox",
    description="Returns all SMS messages sent by the mock provider. Only available in development. "
                "Shows OTPs and ProofLink URLs that would have been sent via real SMS in production.",
)
def get_sms_inbox():
    _require_dev()
    messages = MockSMSProvider.get_sms_log()
    return {
        "environment": settings.ENVIRONMENT,
        "provider": "mock",
        "notice": "DEMO ONLY — These are messages that would be sent via real SMS in production.",
        "count": len(messages),
        "messages": messages,
    }
