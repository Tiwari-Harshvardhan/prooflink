from datetime import datetime, timezone, timedelta

from app.models.citizen import Citizen
from app.models.prooflink import ProofLink


def test_api_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def _register_and_login(client, db_session, *, name, phone, aadhaar, role="CITIZEN"):
    password = "correct-horse-battery"
    if role == "CITIZEN":
        response = client.post("/api/v1/auth/citizen/register", json={"name": name, "phone": phone, "password": password, "aadhaar_number": aadhaar})
        assert response.status_code == 201, response.text
        citizen = db_session.query(Citizen).filter(Citizen.user_id == response.json()["user_id"]).first()
        citizen.phone_verified = True
        db_session.commit()
    else:
        response = client.post("/api/v1/auth/official/register", json={"name": name, "phone": phone, "password": password, "institution_id": "POLICE-MP-001", "official_id": "OFF-TEST"})
        assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"phone": phone, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_secure_instruction_to_payment_flow(client, db_session):
    citizen_headers = _register_and_login(client, db_session, name="Rahul Sharma", phone="+919876543210", aadhaar="1234 5678 9012")
    official_headers = _register_and_login(client, db_session, name="Officer", phone="+919876543211", aadhaar="", role="OFFICIAL")
    created = client.post("/api/v1/official/instructions", headers=official_headers, json={
        "citizen_aadhaar_number": "123456789012", "citizen_phone": "+91 98765 43210", "instruction_id": "abcd#1234",
        "action": "PAYMENT", "amount": 5000, "currency": "INR", "purpose": "License fee", "reference_id": "REF-1234",
        "issued_at": datetime.now(timezone.utc).isoformat(), "due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    })
    assert created.status_code == 201, created.text
    assert "proof" not in created.json()
    prooflink = db_session.query(ProofLink).one()
    assert prooflink.citizen_id and prooflink.official_id and prooflink.instruction_id == "abcd#1234"
    verified = client.post("/api/v1/verify", headers=citizen_headers, json={"prooflink": f"http://localhost:5173/verify?token={prooflink.proof_id}"})
    assert verified.status_code == 200 and verified.json()["status"] == "VERIFIED"
    order = client.post("/api/v1/payments/create-order", headers=citizen_headers, json={"prooflink": prooflink.proof_id})
    assert order.status_code == 200 and order.json()["amount"] == 5000
    paid = client.post("/api/v1/payments/verify", headers=citizen_headers, json={"payment_id": order.json()["payment_id"]})
    assert paid.status_code == 200 and paid.json()["status"] == "PAID"
    dashboard = client.get("/api/v1/dashboard/official/instructions", headers=official_headers)
    assert dashboard.status_code == 200 and dashboard.json()[0]["payment_status"] == "PAID"


def test_citizen_cannot_verify_another_citizens_prooflink(client, db_session):
    owner_headers = _register_and_login(client, db_session, name="Owner", phone="+919876543210", aadhaar="123456789012")
    other_headers = _register_and_login(client, db_session, name="Other", phone="+919876543212", aadhaar="999956789012")
    official_headers = _register_and_login(client, db_session, name="Officer", phone="+919876543211", aadhaar="", role="OFFICIAL")
    response = client.post("/api/v1/official/instructions", headers=official_headers, json={"citizen_aadhaar_number": "123456789012", "citizen_phone": "+919876543210", "instruction_id": "OWN-1", "action": "PAYMENT", "amount": 1, "currency": "INR", "purpose": "Test", "reference_id": "OWN-REF", "issued_at": datetime.now(timezone.utc).isoformat(), "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()})
    assert response.status_code == 201
    proof_id = db_session.query(ProofLink).one().proof_id
    forbidden = client.post("/api/v1/verify", headers=other_headers, json={"prooflink": proof_id})
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["error"] == "PROOFLINK_NOT_OWNED"
    assert client.post("/api/v1/verify", headers=owner_headers, json={"prooflink": proof_id}).status_code == 200


def test_api_institution_endpoints(client):
    res = client.get("/api/v1/institutions/POLICE-MP-001")
    assert res.status_code == 200
    assert "private_key" not in res.json()


def test_api_list_institutions(client):
    assert len(client.get("/api/v1/institutions").json()) >= 5
