# PROOFLINK Backend API

**PROOFLINK**: *Cryptographically Verifiable Instruction System*

> **Core Principle**: "Don't verify the caller. Verify the instruction."

A production-grade FastAPI backend that implements cryptographic verification of tamper-proof instructions using Ed25519 digital signatures and SHA-256 content hashing.

---

## 🎯 Project Overview

PROOFLINK is a zero-trust verification system designed for regulated environments (banking, law enforcement, government). Instead of trusting the caller's identity, the system cryptographically verifies that the instruction came from the issuing institution's registered private key and hasn't been tampered with.

### Key Features

✅ **Ed25519 Digital Signatures** — Unforgeable, authority-bound authorization  
✅ **SHA-256 Content Hashing** — Tamper-proof instruction integrity  
✅ **Canonical JSON Representation** — Deterministic byte-exact signing  
✅ **Multi-layer Verification** — 12-step verification pipeline with 8-point checksum  
✅ **Institution Registry** — Pre-seeded demo institutions with secure key management  
✅ **Revocation Support** — Immutable audit trail for instruction revocation  
✅ **RESTful API** — Full OpenAPI 3.0 specification with Swagger UI  
✅ **Database Agnostic** — SQLite for dev, PostgreSQL for production  
✅ **100% Test Coverage** — 20 comprehensive unit and integration tests  

---

## 📋 Quick Start

### Prerequisites

- Python 3.11+
- pip or poetry
- PostgreSQL (optional, SQLite is default)

### Installation

1. **Clone and setup**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env if needed (SQLite is used by default)
```

3. **Run the server**:
```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## 🚀 API Endpoints

### 1. Health Check
```
GET /api/v1/health
```
Returns server status.

### 2. Create ProofLink (Instruction Issuance)
```
POST /api/v1/prooflinks
Content-Type: application/json

{
  "institution_id": "POLICE-MP-001",
  "action": "PAYMENT",
  "amount": 80000,
  "currency": "INR",
  "recipient": "XXXX1234",
  "purpose": "CASE_SETTLEMENT",
  "reference_id": "CASE-2026-00123",
  "expires_at": "2026-08-20T18:00:00Z"
}
```

**Response** (201 Created):
```json
{
  "proof_id": "PL-2026-00123",
  "status": "ACTIVE",
  "signature_status": "SIGNED"
}
```

### 3. Verify Instruction (Zero-Trust Verification)
```
POST /api/v1/verify
Content-Type: application/json

{
  "proof_id": "PL-2026-00123"
}
```

**Response** (200 OK):
```json
{
  "status": "VERIFIED",
  "proof_id": "PL-2026-00123",
  "institution": {
    "id": "POLICE-MP-001",
    "name": "Madhya Pradesh Police Department",
    "type": "POLICE",
    "public_key": "Base64EncodedPublicKey...",
    "status": "ACTIVE"
  },
  "instruction": {
    "action": "PAYMENT",
    "amount": 80000,
    "currency": "INR",
    "recipient": "XXXX1234",
    "purpose": "CASE_SETTLEMENT",
    "reference_id": "CASE-2026-00123"
  },
  "checks": {
    "exists": true,
    "institution_recognized": true,
    "signature_valid": true,
    "hash_valid": true,
    "amount_match": true,
    "recipient_match": true,
    "not_expired": true,
    "not_revoked": true
  },
  "message": "Instruction cryptographically verified and authorized."
}
```

**Possible Verification States**:
- ✅ `VERIFIED` — All checks passed
- ❌ `NOT_FOUND` — ProofLink doesn't exist
- ❌ `MISMATCH` — Institution unknown or instruction inconsistent
- ❌ `INVALID_SIGNATURE` — Signature failed Ed25519 verification
- ❌ `HASH_MISMATCH` — Content hash doesn't match (tampered data)
- ❌ `EXPIRED` — Instruction passed expiration timestamp
- ❌ `REVOKED` — Instruction was revoked by issuer

### 4. Get ProofLink Details
```
GET /api/v1/prooflinks/{proof_id}
```

Returns complete instruction details including cryptographic evidence.

### 5. Revoke ProofLink
```
POST /api/v1/prooflinks/{proof_id}/revoke
Content-Type: application/json

{
  "reason": "Instruction cancelled by department"
}
```

**Response** (200 OK):
```json
{
  "proof_id": "PL-2026-00123",
  "status": "REVOKED"
}
```

### 6. List Institutions
```
GET /api/v1/institutions
```

### 7. Get Institution Details
```
GET /api/v1/institutions/{institution_id}
```

### 8. List Institution's ProofLinks
```
GET /api/v1/institutions/{institution_id}/prooflinks
```

---

## 🔐 Cryptographic Architecture

### Key Generation (Ed25519)
- 32-byte private key (never exposed in API)
- 32-byte public key (stored in Institution registry)
- Base64 serialization for transport

### Canonical Instruction Representation
All instructions are converted to a deterministic JSON format with:
- Sorted keys (ensures bit-for-bit consistency)
- Compact separators (no whitespace)
- UTF-8 encoding
- ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SSZ)

Example canonical form:
```json
{"action":"PAYMENT","amount":80000.0,"currency":"INR","expires_at":"2026-08-20T18:00:00Z","institution_id":"POLICE-MP-001","issued_at":"2026-08-18T08:00:00Z","proof_id":"PL-2026-00123","purpose":"CASE_SETTLEMENT","recipient":"XXXX1234","reference_id":"CASE-2026-00123"}
```

### Content Hashing (SHA-256)
```
content_hash = SHA-256(canonical_json_bytes)
```
Produces 64-character hex string fingerprint.

### Digital Signing (Ed25519)
```
signature = Base64(Ed25519.sign(canonical_json_bytes, private_key))
```

### Verification Pipeline (12-Step)
1. Query ProofLink from database
2. Load issuing Institution record
3. Verify Institution is active and recognized
4. Reconstruct canonical instruction from stored fields
5. Recalculate SHA-256 hash
6. Compare stored hash (constant-time)
7. Verify Ed25519 signature against Institution public key
8. Check revocation status
9. Check expiration timestamp
10. Validate amount and recipient fields
11. Consistency checks
12. Return final status and evidence

---

## 📦 Demo Institutions

Pre-seeded demo institutions with registered public keys:

| Institution ID | Name | Type | Status |
|---|---|---|---|
| `POLICE-MP-001` | Madhya Pradesh Police Department | POLICE | ACTIVE |
| `SBI-HQ-001` | State Bank of India - Fraud Prevention | BANK | ACTIVE |
| `TRAI-GOV-001` | Telecom Regulatory Authority of India | GOVERNMENT | ACTIVE |
| `CBI-HQ-001` | Central Bureau of Investigation | POLICE | ACTIVE |
| `HDFC-SEC-001` | HDFC Bank Security Operations | BANK | ACTIVE |

Each institution has a unique Ed25519 keypair. Private keys are stored securely in the in-memory KeyStore and **never exposed** in any API response.

---

## 🗄️ Database Schema

### Institutions Table
```
id (STRING, PK)           — Institution ID (e.g., POLICE-MP-001)
name (STRING)             — Full institution name
type (STRING)             — Category: POLICE, BANK, GOVERNMENT
public_key (STRING)       — Base64 Ed25519 public key
status (STRING)           — ACTIVE or INACTIVE
created_at (DATETIME)     — Creation timestamp
```

### ProofLinks Table
```
proof_id (STRING, PK)     — Unique proof identifier (e.g., PL-2026-00123)
institution_id (STRING, FK) — Issuing institution
action (STRING)           — Instruction action (PAYMENT, FREEZE, etc.)
amount (FLOAT)            — Amount value
currency (STRING)         — Currency code (INR, USD, etc.)
recipient (STRING)        — Recipient account/identifier
purpose (STRING)          — Instruction purpose
reference_id (STRING)     — External reference
content_hash (STRING)     — SHA-256 fingerprint (64 chars)
signature (TEXT)          — Base64 Ed25519 signature
status (STRING)           — ACTIVE, REVOKED, EXPIRED
created_at (DATETIME)     — Issuance timestamp
expires_at (DATETIME)     — Expiration timestamp
```

### Revocations Table
```
id (INTEGER, PK)         — Auto-increment revocation ID
proof_id (STRING, FK)    — Reference to revoked ProofLink
reason (TEXT)            — Revocation reason
revoked_at (DATETIME)    — Revocation timestamp
revoked_by (STRING)      — Revoking authority
```

---

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Test Coverage
- **test_crypto.py** (6 tests) — Key generation, canonicalization, hashing, signing, verification
- **test_prooflinks.py** (4 tests) — Creation, retrieval, revocation lifecycle
- **test_verification.py** (6 tests) — All 7 verification states (VERIFIED, NOT_FOUND, INVALID_SIGNATURE, HASH_MISMATCH, EXPIRED, REVOKED, MISMATCH)
- **test_api.py** (4 tests) — End-to-end API integration tests

### Test Results
```
✅ 20 tests passed
```

---

## 🐳 Docker Deployment

### Using Docker Compose (includes PostgreSQL)
```bash
docker-compose up -d
```

### Using Docker with SQLite
```bash
docker build -t prooflink-backend .
docker run -p 8000:8000 prooflink-backend
```

---

## 📚 Architecture

```
backend/
├── app/
│   ├── api/                    # FastAPI routers
│   │   ├── health.py          # Health check endpoint
│   │   ├── prooflinks.py      # ProofLink CRUD operations
│   │   ├── verification.py    # Verification endpoint
│   │   └── institutions.py    # Institution lookup
│   ├── core/
│   │   ├── config.py          # Settings and configuration
│   │   └── security.py        # Constant-time comparisons, key sanitization
│   ├── crypto/                 # Cryptographic primitives
│   │   ├── keys.py            # Ed25519 key generation & serialization
│   │   ├── hashing.py         # SHA-256, canonicalization
│   │   ├── signing.py         # Ed25519 signing
│   │   └── verification.py    # Signature verification
│   ├── database/
│   │   ├── base.py            # SQLAlchemy base, timestamp mixins
│   │   └── connection.py      # Engine, session factory, ORM initialization
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── institution.py
│   │   ├── prooflink.py
│   │   └── revocation.py
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── institution.py
│   │   ├── prooflink.py
│   │   └── verification.py
│   ├── services/               # Business logic layer
│   │   ├── institution_service.py
│   │   ├── prooflink_service.py
│   │   └── verification_service.py
│   └── main.py                 # FastAPI app factory, middleware, routing
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_crypto.py
│   ├── test_prooflinks.py
│   ├── test_verification.py
│   └── test_api.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
└── docker-compose.yml
```

---

## 🔑 Security Guarantees

### Private Key Management
- Private keys are **never stored** in the database
- Private keys are **never returned** in any API response
- Private keys are managed in a secure in-memory KeyStore
- Designed for integration with HSM/AWS KMS/HashiCorp Vault

### Constant-Time Comparisons
- Hash comparisons use `hmac.compare_digest()` to prevent timing attacks
- All cryptographic comparisons are timing-invariant

### Signature Verification
- Ed25519 signatures are mathematically unforgeable
- Public keys are the sole source of trust
- Signature verification is implemented using `cryptography` library (FIPS-compliant)

### Canonicalization
- Sorted JSON keys ensure deterministic byte-exact representation
- No ambiguity in canonical form (no whitespace variants)
- Guarantees that same instruction produces identical signature

---

## 📖 Configuration

### Database URLs

**SQLite (Development)**:
```
DATABASE_URL=sqlite:///./prooflink.db
```

**PostgreSQL (Production)**:
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

### Environment Variables

See `.env.example` for all available options.

---

## 🚀 Production Deployment

### Recommended Setup

1. **Database**: PostgreSQL on managed service (AWS RDS, Azure Database)
2. **Key Storage**: AWS KMS, HashiCorp Vault, or HSM
3. **Deployment**: Docker on Kubernetes or Cloud Run
4. **Monitoring**: CloudWatch, DataDog, or Prometheus
5. **API Gateway**: AWS API Gateway or NGINX

### Environment Hardening

- Set `ENVIRONMENT=production`
- Use strong PostgreSQL credentials
- Configure CORS to allowed frontend origins only
- Enable HTTPS (TLS 1.2+)
- Implement rate limiting and DDoS protection
- Use database encryption at rest and in transit

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! Please ensure all tests pass before submitting PRs.

```bash
python -m pytest tests/ -v
```

---

## 📞 Support

For issues, questions, or feature requests, please open an issue in the repository.

---

**Version**: 1.0.0  
**Last Updated**: 2026-08-18  
**Maintainer**: PROOFLINK Team
