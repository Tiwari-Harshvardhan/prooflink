from __future__ import annotations

from abc import ABC, abstractmethod
from app.core.config import settings


class KYCService(ABC):
    @abstractmethod
    def verify_identity(self, full_name: str, aadhaar_number: str, phone_number: str) -> dict:
        raise NotImplementedError


class MockKYCProvider(KYCService):
    def verify_identity(self, full_name: str, aadhaar_number: str, phone_number: str) -> dict:
        return {
            "status": "VERIFIED",
            "provider": "mock_kyc",
            "message": "DEMO KYC / SANDBOX verification successful.",
            "aadhaar_reference": f"KYC-{abs(hash((full_name, aadhaar_number, phone_number))) % 100000000:08d}",
            "masked_aadhaar": "XXXX XXXX " + aadhaar_number[-4:],
        }


class RealKYCProvider(KYCService):
    def verify_identity(self, full_name: str, aadhaar_number: str, phone_number: str) -> dict:
        raise NotImplementedError("Real KYC provider integration must be configured.")


def get_kyc_service() -> KYCService:
    if settings.KYC_PROVIDER.lower() != "mock":
        raise RuntimeError("Only the clearly labelled mock KYC provider is configured for this MVP.")
    return MockKYCProvider()
