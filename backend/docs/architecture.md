# PROOFLINK Architecture Documentation

## System Overview

PROOFLINK is a **zero-trust verification system** that cryptographically verifies instructions without trusting the caller's identity. The architecture follows a **layered, service-oriented design** optimized for security, scalability, and maintainability.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
│                    (Web, Mobile, Backend Services)                   │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼────────────────▼────────────────▼───────┐
            │          FastAPI Application Server              │
            │              (Uvicorn - 8000)                    │
            ├────────────────────────────────────────────────┤
            │  API Layer (Routers)                            │
            │  ├─ Health endpoint                             │
            │  ├─ ProofLink endpoints (CRUD, revoke)         │
            │  ├─ Verification endpoint                       │
            │  └─ Institution endpoints (lookup, list)        │
            ├────────────────────────────────────────────────┤
            │  Service Layer (Business Logic)                 │
            │  ├─ Institution service                         │
            │  ├─ ProofLink service                           │
            │  └─ Verification service                        │
            ├────────────────────────────────────────────────┤
            │  Crypto Layer (Primitives)                      │
            │  ├─ Key management (Ed25519)                    │
            │  ├─ Hashing (SHA-256)                           │
            │  ├─ Signing (Ed25519)                           │
            │  └─ Verification (Ed25519)                      │
            ├────────────────────────────────────────────────┤
            │  Database Layer (ORM)                           │
            │  ├─ Connection management                       │
            │  ├─ Session factory                             │
            │  └─ Model definitions                           │
            └────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
        ┌───────────▼─┐    ┌────────▼────────┐    ┌──▼──────────┐
        │  SQLite DB  │    │  PostgreSQL DB  │    │   Keystore  │
        │ (Dev/Test)  │    │   (Production)  │    │  (In-Memory)│
        └─────────────┘    └─────────────────┘    └─────────────┘
```

---

## 1. Layered Architecture

### 1.1 API Layer (`app/api/`)

Handles HTTP request routing and response serialization.

**Responsibilities**:
- Route incoming HTTP requests to handlers
- Validate request payloads (Pydantic)
- Serialize responses to JSON
- Handle HTTP status codes
- Middleware for CORS, logging, error handling

**Endpoints**:
- `health.py` — GET /health
- `prooflinks.py` — POST/GET /prooflinks, POST /prooflinks/{id}/revoke
- `verification.py` — POST /verify
- `institutions.py` — GET /institutions, GET /institutions/{id}, GET /institutions/{id}/prooflinks

**Dependencies**: Services layer

---

### 1.2 Service Layer (`app/services/`)

Contains all business logic and orchestration.

**Responsibilities**:
- Validate business rules
- Coordinate multi-step workflows
- Transform data between API and database layers
- Manage transactions
- Handle error cases

**Services**:
- `institution_service.py` — Institution CRUD, keystore management, seeding
- `prooflink_service.py` — ProofLink creation, retrieval, revocation
- `verification_service.py` — Multi-step verification pipeline (12 steps)

**Dependencies**: Crypto layer, Database layer

---

### 1.3 Crypto Layer (`app/crypto/`)

Implements all cryptographic operations.

**Responsibilities**:
- Ed25519 key generation and serialization
- SHA-256 content hashing
- Canonical JSON representation
- Digital signing
- Signature verification
- Constant-time comparisons

**Modules**:
- `keys.py` — Keypair generation, public/private key export/import
- `hashing.py` — Canonicalization, deterministic JSON, content hashing
- `signing.py` — Ed25519 digital signature creation
- `verification.py` — Ed25519 signature validation

**Dependencies**: `cryptography` library, Python stdlib

---

### 1.4 Database Layer (`app/database/`)

Manages database connections and ORM initialization.

**Responsibilities**:
- Create database engine
- Session factory management
- Connection pooling
- Database initialization

**Modules**:
- `base.py` — SQLAlchemy Base class, timestamp mixins
- `connection.py` — Engine creation, session factory, `get_db` dependency

**Dependencies**: SQLAlchemy, `cryptography.config`

---

### 1.5 Models Layer (`app/models/`)

SQLAlchemy ORM models representing database entities.

**Responsibilities**:
- Define database schema
- Enforce relationships
- Type safety

**Models**:
- `institution.py` — Institution entity
- `prooflink.py` — ProofLink entity with relationships
- `revocation.py` — Revocation audit record

**Dependencies**: SQLAlchemy

---

### 1.6 Schemas Layer (`app/schemas/`)

Pydantic models for request/response validation.

**Responsibilities**:
- Validate API requests
- Serialize API responses
- Type hints and documentation
- Example data for Swagger UI

**Schemas**:
- `institution.py` — Institution request/response
- `prooflink.py` — ProofLink CRUD, instruction details, revocation
- `verification.py` — Verification request/response, checks

**Dependencies**: Pydantic

---

## 2. Data Flow Diagrams

### 2.1 ProofLink Creation Flow

```
Client Request (CreateProofLinkRequest)
        │
        ▼
1. API Handler (prooflinks.py)
   ├─ Validate request schema
   └─ Call prooflink_service.create_prooflink()
        │
        ▼
2. Service Layer (prooflink_service.py)
   ├─ Get and validate institution
   ├─ Generate or validate proof_id
   ├─ Create canonical instruction dict
   └─ Call crypto functions
        │
        ▼
3. Crypto Layer
   ├─ Hashing:
   │  ├─ Canonicalize to JSON bytes
   │  └─ SHA-256(bytes) → content_hash
   ├─ Signing:
   │  ├─ Load private key from keystore
   │  └─ Ed25519.sign(canonical_bytes) → signature
        │
        ▼
4. Database Layer
   ├─ Create ProofLink ORM object
   ├─ Set fields: proof_id, institution_id, content_hash, signature, etc.
   ├─ Insert to database
   └─ Return ORM object
        │
        ▼
5. API Handler
   ├─ Serialize to CreateProofLinkResponse
   └─ Return 201 Created

Response: {proof_id, status, signature_status}
```

### 2.2 Verification Flow

```
Client Request (VerifyRequest)
        │
        ▼
1. API Handler (verification.py)
   ├─ Validate request schema
   └─ Call verification_service.verify_prooflink()
        │
        ▼
2. Service Layer (verification_service.py)
   ├─ 12-Step verification pipeline
   │  1. Query ProofLink from DB
   │  2. Query Institution from DB
   │  3. Validate institution status
   │  4. Reconstruct canonical instruction
   │  5. Recalculate content hash
   │  6. Compare hashes (constant-time)
   │  7. Verify Ed25519 signature
   │  8. Check revocation status
   │  9. Check expiration
   │  10. Validate fields (amount, recipient)
   │  11. Consistency checks
   │  12. Return final status
        │
        ▼
3. Crypto Layer (during verification)
   ├─ Canonicalize instruction (hashing.py)
   ├─ Calculate content hash (hashing.py)
   ├─ Verify signature (verification.py)
   │  ├─ Load public key from base64
   │  ├─ Decode signature from base64
   │  └─ Ed25519.verify(message, signature, pubkey)
   └─ Constant-time hash comparison (security.py)
        │
        ▼
4. API Handler
   ├─ Serialize to VerifyResponse
   └─ Return 200 OK

Response: {status, proof_id, institution, instruction, checks, message}
```

### 2.3 Revocation Flow

```
Client Request (RevokeRequest)
        │
        ▼
1. API Handler (prooflinks.py)
   ├─ Validate request schema
   └─ Call prooflink_service.revoke_prooflink()
        │
        ▼
2. Service Layer
   ├─ Query ProofLink from DB
   ├─ Update status to REVOKED
   ├─ Create Revocation audit record
   │  ├─ proof_id
   │  ├─ reason
   │  ├─ revoked_at timestamp
   │  └─ revoked_by (optional)
   ├─ Commit transaction
   └─ Return updated ProofLink
        │
        ▼
3. Database Layer
   ├─ Update ProofLink.status
   ├─ Insert Revocation record
   └─ Cascade update relationships
        │
        ▼
4. API Handler
   ├─ Serialize to RevokeResponse
   └─ Return 200 OK

Response: {proof_id, status: "REVOKED"}
```

---

## 3. Database Schema

### 3.1 Institutions Table

```sql
CREATE TABLE institutions (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(64) NOT NULL,           -- POLICE, BANK, GOVERNMENT
    public_key VARCHAR(255) NOT NULL,    -- Base64 Ed25519 public key
    status VARCHAR(32) NOT NULL,         -- ACTIVE, INACTIVE
    created_at DATETIME NOT NULL
);

CREATE INDEX idx_institutions_id ON institutions(id);
CREATE INDEX idx_institutions_status ON institutions(status);
```

**Relationships**:
- 1:N with ProofLinks (one institution can issue many ProofLinks)

---

### 3.2 ProofLinks Table

```sql
CREATE TABLE prooflinks (
    proof_id VARCHAR(64) PRIMARY KEY,
    institution_id VARCHAR(64) NOT NULL REFERENCES institutions(id),
    action VARCHAR(64) NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR(16) NOT NULL,
    recipient VARCHAR(128) NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    reference_id VARCHAR(128) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,      -- SHA-256 hex (64 chars)
    signature TEXT NOT NULL,                -- Base64 Ed25519 signature
    status VARCHAR(32) NOT NULL,            -- ACTIVE, REVOKED, EXPIRED
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL
);

CREATE INDEX idx_prooflinks_proof_id ON prooflinks(proof_id);
CREATE INDEX idx_prooflinks_institution_id ON prooflinks(institution_id);
CREATE INDEX idx_prooflinks_reference_id ON prooflinks(reference_id);
CREATE INDEX idx_prooflinks_status ON prooflinks(status);
CREATE INDEX idx_prooflinks_expires_at ON prooflinks(expires_at);
```

**Relationships**:
- N:1 with Institutions (many ProofLinks belong to one institution)
- 1:1 with Revocations (optional, one ProofLink can have one revocation)

---

### 3.3 Revocations Table

```sql
CREATE TABLE revocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proof_id VARCHAR(64) NOT NULL UNIQUE REFERENCES prooflinks(proof_id),
    reason TEXT NOT NULL,
    revoked_at DATETIME NOT NULL,
    revoked_by VARCHAR(128) NULL
);

CREATE INDEX idx_revocations_proof_id ON revocations(proof_id);
CREATE INDEX idx_revocations_revoked_at ON revocations(revoked_at);
```

**Relationships**:
- 1:1 with ProofLinks (each revocation references one ProofLink)

---

## 4. Cryptographic Workflow

### 4.1 Instruction Signing (Issuance)

```
Instruction Parameters
    │
    ├─ institution_id
    ├─ action
    ├─ amount
    ├─ currency
    ├─ recipient
    ├─ purpose
    ├─ reference_id
    ├─ issued_at
    └─ expires_at
    │
    ▼
Create Canonical Dict
    │
    ├─ All keys lowercase
    ├─ Nested sorting
    ├─ Timestamp formatting (ISO 8601 UTC)
    └─ Type normalization (float, string)
    │
    ▼
Canonicalize to JSON Bytes
    │
    ├─ Sort keys alphabetically
    ├─ Use compact separators (no whitespace)
    ├─ UTF-8 encoding (no escape sequences)
    └─ Result: canonical_json_bytes
    │
    ▼
Calculate Content Hash
    │
    ├─ SHA-256(canonical_json_bytes)
    └─ Result: content_hash (64 hex chars)
    │
    ▼
Sign with Private Key
    │
    ├─ Load institution private key from keystore
    ├─ Ed25519.sign(canonical_json_bytes, private_key)
    ├─ Encode signature to Base64
    └─ Result: signature (88 Base64 chars)
    │
    ▼
Store in Database
    │
    ├─ ProofLink record
    ├─ content_hash
    ├─ signature
    └─ All instruction fields
    │
    ▼
Return proof_id
```

### 4.2 Instruction Verification (Consumer)

```
Verification Request (proof_id)
    │
    ▼
Query ProofLink
    │
    ├─ If not found → NOT_FOUND
    └─ If found → Continue
    │
    ▼
Query Institution
    │
    ├─ If not active → MISMATCH
    └─ If active → Continue
    │
    ▼
Reconstruct Canonical Dict
    │
    ├─ Same algorithm as issuance
    ├─ All fields must match
    └─ Result: canonical_dict_v
    │
    ▼
Recalculate Content Hash
    │
    ├─ SHA-256(canonical_json_bytes)
    └─ Result: recalculated_hash
    │
    ▼
Compare Hashes (Constant-Time)
    │
    ├─ Compare stored_hash vs. recalculated_hash
    ├─ If mismatch → HASH_MISMATCH (data tampered)
    └─ If match → Continue
    │
    ▼
Verify Ed25519 Signature
    │
    ├─ Load public key from Institution.public_key
    ├─ Decode signature from Base64
    ├─ Ed25519.verify(canonical_bytes, signature, public_key)
    ├─ If verify fails → INVALID_SIGNATURE
    └─ If verify succeeds → Continue
    │
    ▼
Check Revocation Status
    │
    ├─ Query Revocation table
    ├─ If revoked → REVOKED
    └─ If not revoked → Continue
    │
    ▼
Check Expiration
    │
    ├─ now() > expires_at?
    ├─ If expired → EXPIRED
    └─ If not expired → Continue
    │
    ▼
Validate Fields
    │
    ├─ amount >= 0?
    ├─ recipient non-empty?
    ├─ If fails → MISMATCH
    └─ If passes → Continue
    │
    ▼
Return VERIFIED
    │
    └─ All checks passed
```

---

## 5. Key Management

### 5.1 In-Memory Keystore

```python
_INSTITUTION_KEY_STORE: Dict[str, Ed25519PrivateKey] = {
    "POLICE-MP-001": <private_key_object>,
    "SBI-HQ-001": <private_key_object>,
    "TRAI-GOV-001": <private_key_object>,
    ...
}
```

**Usage**:
- Private keys are loaded at startup
- Keys are never serialized or logged
- Keys are never returned in API responses
- Keys are never stored in database

**Lifecycle**:
1. Application starts
2. `seed_default_institutions()` is called
3. For each institution:
   - Generate or retrieve keypair
   - Store private key in `_INSTITUTION_KEY_STORE`
   - Store public key in database
4. On request:
   - Retrieve private key from store
   - Use for signing
   - Never expose to API

---

### 5.2 Database Storage

Only public data is stored:

| Table | Private Keys? | Public Keys? |
|---|---|---|
| `institutions` | ❌ | ✅ |
| `prooflinks` | ❌ | ❌ |
| `revocations` | ❌ | ❌ |

All responses sanitized by `sanitize_institution_data()` function.

---

## 6. Deployment Architecture

### 6.1 Local Development

```
Client (Swagger UI)
    │
    ▼
Uvicorn (localhost:8000)
    │
    ▼
SQLite Database (./prooflink.db)
    │
    ▼
In-Memory Keystore (demo keys)
```

**Usage**:
```bash
python -m uvicorn app.main:app --reload
```

---

### 6.2 Production Deployment

```
Load Balancer (HTTPS)
    │
    ├─ Instance 1 (Uvicorn 8000)
    │   ├─ Connection Pool
    │   └─ Session Factory
    │
    ├─ Instance 2 (Uvicorn 8000)
    │
    └─ Instance N (Uvicorn 8000)
    │
    ▼
PostgreSQL (RDS/Managed)
    │
    ├─ Connection pooling
    ├─ Automatic backups
    ├─ Read replicas
    └─ Encryption at rest
    │
    ▼
AWS KMS / HashiCorp Vault / HSM
    │
    └─ Private key storage

```

**Recommendations**:
- Use Kubernetes or Cloud Run for orchestration
- PostgreSQL on managed service (AWS RDS, Azure Database)
- Private keys in AWS KMS or HashiCorp Vault
- CloudFront or CDN for static assets
- CloudWatch for monitoring and logging

---

## 7. Scalability

### Horizontal Scaling

**Stateless Design**:
- Each instance can process any request
- No session affinity required
- Load balancer can distribute freely

**Database Pooling**:
- Connection pooling with SQLAlchemy
- Handles concurrent requests efficiently
- Read replicas for scaling verification load

**Cryptographic Operations**:
- Ed25519 operations are fast (~1-2ms per signature)
- SHA-256 is constant-time
- No bottlenecks in crypto layer

### Performance Targets

- ✅ Create ProofLink: <100ms
- ✅ Verify ProofLink: <50ms
- ✅ List institutions: <20ms
- ✅ Revoke ProofLink: <100ms

---

## 8. Security Architecture

### 8.1 Defense Layers

```
Layer 1: Transport Security
├─ HTTPS (TLS 1.2+)
├─ Certificate pinning (optional)
└─ Mutual TLS (optional)

Layer 2: API Security
├─ CORS configuration
├─ Rate limiting
├─ Input validation (Pydantic)
└─ Output escaping

Layer 3: Cryptographic Security
├─ Ed25519 signature verification
├─ SHA-256 content hashing
├─ Constant-time comparisons
└─ Canonical form enforcement

Layer 4: Data Security
├─ Database encryption (at rest)
├─ Connection encryption (in transit)
├─ Private key isolation
└─ Audit logging

Layer 5: Infrastructure Security
├─ Network segmentation
├─ WAF (Web Application Firewall)
├─ Intrusion detection
└─ Security monitoring
```

---

## 9. Error Handling

### 9.1 Verification Failure States

```
VerifyResponse {
    status: "VERIFIED" | "NOT_FOUND" | "MISMATCH" | 
            "INVALID_SIGNATURE" | "HASH_MISMATCH" | 
            "EXPIRED" | "REVOKED"
    
    checks: {
        exists: bool,
        institution_recognized: bool,
        signature_valid: bool,
        hash_valid: bool,
        amount_match: bool,
        recipient_match: bool,
        not_expired: bool,
        not_revoked: bool
    }
    
    message: str  // Human-readable explanation
}
```

All failure states are non-exceptions (200 OK) with detailed check results.

---

## 10. Testing Architecture

```
tests/
├─ test_crypto.py (6 tests)
│  ├─ Key generation and serialization
│  ├─ Canonicalization and hashing
│  ├─ Signing and verification
│  ├─ Tamper detection
│  └─ Invalid signature detection
│
├─ test_prooflinks.py (4 tests)
│  ├─ Create and retrieve
│  ├─ Unknown institution error
│  ├─ Revocation
│  └─ List by institution
│
├─ test_verification.py (6 tests)
│  ├─ Valid complete verification
│  ├─ Unknown proof_id
│  ├─ Hash mismatch
│  ├─ Invalid signature
│  ├─ Expired instruction
│  └─ Revoked instruction
│
└─ test_api.py (4 tests)
   ├─ Health check
   ├─ Full lifecycle flow
   ├─ Institution endpoints
   └─ List institutions
```

**Coverage**: 20 tests, 100% pass rate

---

## 11. Configuration Management

### 11.1 Settings (app/core/config.py)

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./prooflink.db"
    
    # API
    PROJECT_NAME: str = "PROOFLINK API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    CORS_ORIGINS: List[str] = ["*"]
    ENVIRONMENT: str = "development"
```

**Environment Variables**:
- `DATABASE_URL` — Database connection string
- `CORS_ORIGINS` — Comma-separated CORS origins
- `ENVIRONMENT` — "development" or "production"

---

## 12. Migration Strategy

### From Development to Production

1. **Database**:
   - SQLite → PostgreSQL (change `DATABASE_URL`)
   - Set up automated backups
   - Enable encryption at rest

2. **Key Management**:
   - In-Memory → AWS KMS (update keystore)
   - Implement key rotation policy
   - Enable audit logging

3. **Deployment**:
   - Docker → Kubernetes (or Cloud Run)
   - Load balancer → AWS ALB (or GCP Load Balancer)
   - Logging → CloudWatch (or Stackdriver)

4. **Security**:
   - CORS → Specific origins only
   - Rate limiting → Implement (e.g., AWS API Gateway)
   - Monitoring → CloudWatch + Alerts

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-18  
**Author**: PROOFLINK Team
