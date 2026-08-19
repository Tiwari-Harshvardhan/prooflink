from __future__ import annotations

from abc import ABC, abstractmethod
import base64
import logging
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level in-memory SMS log — populated by MockSMSProvider.
# This powers the /dev/sms-inbox developer endpoint for demo purposes.
_SMS_LOG: List[dict] = []
_MAX_LOG_SIZE = 50


class SMSService(ABC):
    @abstractmethod
    def send_sms(self, phone_number: str, message: str) -> dict:
        raise NotImplementedError


class MockSMSProvider(SMSService):
    def send_sms(self, phone_number: str, message: str) -> dict:
        logger.warning("DEMO SMS to %s:\n%s", phone_number, message)
        entry = {
            "id": len(_SMS_LOG) + 1,
            "provider": "mock",
            "phone_number": phone_number,
            "message": message,
            "status": "queued",
            "demo": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _SMS_LOG.append(entry)
        # Keep list bounded
        if len(_SMS_LOG) > _MAX_LOG_SIZE:
            _SMS_LOG.pop(0)
        return entry

    @staticmethod
    def get_sms_log() -> List[dict]:
        """Return in-memory SMS log (most recent last)."""
        return list(reversed(_SMS_LOG))


class RealSMSProvider(SMSService):
    def send_sms(self, phone_number: str, message: str) -> dict:
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_FROM_NUMBER]):
            raise RuntimeError("Twilio is selected but TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_FROM_NUMBER is missing.")
        endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        body = urlencode({"To": phone_number, "From": settings.TWILIO_FROM_NUMBER, "Body": message}).encode()
        credentials = base64.b64encode(f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}".encode()).decode()
        request = Request(endpoint, data=body, headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"})
        with urlopen(request, timeout=15) as response:  # nosec B310 - fixed Twilio HTTPS endpoint
            import json
            payload = json.loads(response.read().decode())
        return {"provider": "twilio", "status": payload.get("status", "queued"), "message_sid": payload.get("sid")}


def get_sms_service() -> SMSService:
    if settings.SMS_PROVIDER.lower() == "twilio":
        return RealSMSProvider()
    return MockSMSProvider()
