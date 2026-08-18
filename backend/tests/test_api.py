import pytest
from datetime import datetime, timezone, timedelta

def test_api_health(client):
    """Endpoint 1 — Health check API."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_create_and_verify_prooflink_flow(client):
    """Endpoints 2, 3, 4, 5, 6 full lifecycle integration test."""
    expires_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    # 1. Create ProofLink
    create_payload = {
        "institution_id": "POLICE-MP-001",
        "action": "PAYMENT",
        "amount": 80000,
        "currency": "INR",
        "recipient": "XXXX1234",
        "purpose": "CASE_SETTLEMENT",
        "reference_id": "CASE-2026-00123",
        "expires_at": expires_at
    }
    
    create_res = client.post("/api/v1/prooflinks", json=create_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["proof_id"] == "PL-2026-00123"
    assert created_data["status"] == "ACTIVE"
    assert created_data["signature_status"] == "SIGNED"
    
    proof_id = created_data["proof_id"]
    
    # 2. Get ProofLink details (for frontend)
    get_res = client.get(f"/api/v1/prooflinks/{proof_id}")
    assert get_res.status_code == 200
    details = get_res.json()
    assert details["proof_id"] == proof_id
    assert details["instruction"]["amount"] == 80000.0
    assert details["instruction"]["action"] == "PAYMENT"
    assert details["institution"]["name"] == "Madhya Pradesh Police Department"
    
    # 3. Verify ProofLink
    verify_res = client.post("/api/v1/verify", json={"proof_id": proof_id})
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["status"] == "VERIFIED"
    assert verify_data["checks"]["exists"] is True
    assert verify_data["checks"]["signature_valid"] is True
    assert verify_data["checks"]["hash_valid"] is True
    assert verify_data["checks"]["not_expired"] is True
    assert verify_data["checks"]["not_revoked"] is True
    
    # 4. Revoke ProofLink
    revoke_res = client.post(f"/api/v1/prooflinks/{proof_id}/revoke", json={"reason": "Instruction cancelled"})
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"
    
    # 5. Verify again -> status should now be REVOKED
    reverify_res = client.post("/api/v1/verify", json={"proof_id": proof_id})
    assert reverify_res.status_code == 200
    assert reverify_res.json()["status"] == "REVOKED"
    assert reverify_res.json()["checks"]["not_revoked"] is False

def test_api_institution_endpoints(client):
    """Endpoint 6 — Institution details and security checks."""
    res = client.get("/api/v1/institutions/POLICE-MP-001")
    assert res.status_code == 200
    data = res.json()
    assert data["institution_id"] == "POLICE-MP-001"
    assert data["name"] == "Madhya Pradesh Police Department"
    assert data["type"] == "POLICE"
    assert "public_key" in data
    
    # SECURITY INVARIANT: Private key must NEVER be exposed
    assert "private_key" not in data
    assert "privkey" not in data
    assert "secret" not in data

def test_api_list_institutions(client):
    res = client.get("/api/v1/institutions")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 5
