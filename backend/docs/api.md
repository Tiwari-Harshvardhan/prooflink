# PROOFLINK API Documentation

## Overview

The PROOFLINK API is a cryptographically verifiable instruction system that implements zero-trust verification. All API endpoints are versioned under `/api/v1`.

**Base URL**: `http://localhost:8000/api/v1`

**OpenAPI Specification**: Available at `/openapi.json`  
**Swagger UI**: Available at `/docs`  
**ReDoc**: Available at `/redoc`

---

## Authentication

The PROOFLINK API does **not use traditional authentication**. Instead, it implements zero-trust verification:

- Instructions are digitally signed with Ed25519 by the issuing institution's private key
- All verification is cryptographic, not identity-based
- The system verifies the **instruction's authenticity**, not the caller's identity

---

## Request/Response Format

### Request Headers
```
Content-Type: application/json
```

### Response Format
All responses follow this structure:

**Success (2xx)**:
```json
{
  "result": {...}
}
```

**Error (4xx, 5xx)**:
```json
{
  "detail": "Error message"
}
```

---

## Endpoints

### 1. Health Check

**Endpoint**: `GET /health`

**Summary**: Server health status

**Response** (200 OK):
```json
{
  "status": "healthy"
}
```

---

### 2. Create ProofLink

**Endpoint**: `POST /prooflinks`

**Summary**: Issue a cryptographically signed instruction

**Request Body**:
```json
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

**Field Descriptions**:

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| `institution_id` | string | Yes | Institution ID from registry | `POLICE-MP-001` |
| `action` | string | Yes | Instruction action type | `PAYMENT`, `FREEZE`, `SUSPEND` |
| `amount` | number | Yes | Numeric amount | `80000` |
| `currency` | string | No | Currency code (default: INR) | `INR`, `USD` |
| `recipient` | string | Yes | Account/identifier | `XXXX1234` |
| `purpose` | string | Yes | Instruction purpose | `CASE_SETTLEMENT` |
| `reference_id` | string | Yes | External reference | `CASE-2026-00123` |
| `expires_at` | string (ISO8601) | Yes | Expiration timestamp UTC | `2026-08-20T18:00:00Z` |

**Response** (201 Created):
```json
{
  "proof_id": "PL-2026-00123",
  "status": "ACTIVE",
  "signature_status": "SIGNED"
}
```

**Response Fields**:

| Field | Type | Description |
|---|---|---|
| `proof_id` | string | Unique proof identifier |
| `status` | string | Current status (ACTIVE, REVOKED, EXPIRED) |
| `signature_status` | string | Signature status (SIGNED, UNSIGNED) |

**Errors**:
- `400 Bad Request` — Invalid institution or missing fields
- `404 Not Found` — Institution not found
- `500 Internal Server Error` — Signing failed

---

### 3. Verify Instruction

**Endpoint**: `POST /verify`

**Summary**: Cryptographically verify an instruction's authenticity

**Request Body**:
```json
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
    "public_key": "Base64PublicKey...",
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

**Response Fields**:

| Field | Type | Description |
|---|---|---|
| `status` | string | Verification status (see below) |
| `proof_id` | string | Requested proof ID |
| `institution` | object | Issuing institution details |
| `instruction` | object | Instruction data |
| `checks` | object | Verification checklist (8 boolean fields) |
| `message` | string | Human-readable verification result |

**Verification Status Values**:

| Status | Meaning | HTTP | checks.exists |
|---|---|---|---|
| `VERIFIED` | ✅ All cryptographic and business checks passed | 200 | `true` |
| `NOT_FOUND` | ❌ ProofLink doesn't exist in registry | 200 | `false` |
| `MISMATCH` | ❌ Institution unknown or instruction inconsistent | 200 | `true` |
| `INVALID_SIGNATURE` | ❌ Ed25519 signature verification failed | 200 | `true` |
| `HASH_MISMATCH` | ❌ Content hash doesn't match (data tampered) | 200 | `true` |
| `EXPIRED` | ❌ Instruction passed expiration timestamp | 200 | `true` |
| `REVOKED` | ❌ Instruction was revoked by issuer | 200 | `true` |

**Verification Checks Breakdown**:

```typescript
interface VerificationChecks {
  exists: boolean;                      // ProofLink exists in database
  institution_recognized: boolean;      // Institution is registered and active
  signature_valid: boolean;             // Ed25519 signature verified
  hash_valid: boolean;                  // SHA-256 content hash matches
  amount_match: boolean;                // Amount field is valid
  recipient_match: boolean;             // Recipient field is valid
  not_expired: boolean;                 // Instruction not past expiration
  not_revoked: boolean;                 // Instruction not revoked
}
```

---

### 4. Get ProofLink Details

**Endpoint**: `GET /prooflinks/{proof_id}`

**Summary**: Retrieve full instruction details with cryptographic evidence

**Path Parameters**:
- `proof_id` (string, required) — Proof ID (e.g., `PL-2026-00123`)

**Response** (200 OK):
```json
{
  "proof_id": "PL-2026-00123",
  "institution": {
    "id": "POLICE-MP-001",
    "name": "Madhya Pradesh Police Department",
    "type": "POLICE",
    "public_key": "Base64PublicKey...",
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
  "content_hash": "abc123def456...",
  "signature": "Base64EncodedSignature...",
  "status": "ACTIVE",
  "created_at": "2026-08-18T08:00:00Z",
  "expires_at": "2026-08-20T18:00:00Z"
}
```

**Errors**:
- `404 Not Found` — Proof ID doesn't exist

---

### 5. Revoke ProofLink

**Endpoint**: `POST /prooflinks/{proof_id}/revoke`

**Summary**: Revoke an active instruction and create immutable audit record

**Path Parameters**:
- `proof_id` (string, required) — Proof ID to revoke

**Request Body**:
```json
{
  "reason": "Instruction cancelled by department"
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|---|---|---|---|
| `reason` | string | Yes | Revocation reason for audit trail |

**Response** (200 OK):
```json
{
  "proof_id": "PL-2026-00123",
  "status": "REVOKED"
}
```

**Errors**:
- `404 Not Found` — Proof ID doesn't exist
- `400 Bad Request` — Invalid revocation request

---

### 6. List Institutions

**Endpoint**: `GET /institutions`

**Summary**: List all registered institutions and their public keys

**Query Parameters**: None

**Response** (200 OK):
```json
[
  {
    "institution_id": "POLICE-MP-001",
    "name": "Madhya Pradesh Police Department",
    "type": "POLICE",
    "public_key": "Base64PublicKey...",
    "status": "ACTIVE"
  },
  {
    "institution_id": "SBI-HQ-001",
    "name": "State Bank of India - Fraud Prevention Unit",
    "type": "BANK",
    "public_key": "Base64PublicKey...",
    "status": "ACTIVE"
  }
]
```

---

### 7. Get Institution Details

**Endpoint**: `GET /institutions/{institution_id}`

**Summary**: Retrieve a specific institution's public registry data

**Path Parameters**:
- `institution_id` (string, required) — Institution ID (e.g., `POLICE-MP-001`)

**Response** (200 OK):
```json
{
  "institution_id": "POLICE-MP-001",
  "name": "Madhya Pradesh Police Department",
  "type": "POLICE",
  "public_key": "Base64PublicKey...",
  "status": "ACTIVE"
}
```

**Response Fields**:

| Field | Type | Description |
|---|---|---|
| `institution_id` | string | Unique institution identifier |
| `name` | string | Full institution name |
| `type` | string | Institution type (POLICE, BANK, GOVERNMENT) |
| `public_key` | string | Base64-encoded Ed25519 public key |
| `status` | string | Status (ACTIVE, INACTIVE) |

**Security Note**: Private keys are **never returned** in any API response.

**Errors**:
- `404 Not Found` — Institution not found

---

### 8. List Institution's ProofLinks

**Endpoint**: `GET /institutions/{institution_id}/prooflinks`

**Summary**: Retrieve all ProofLinks issued by a specific institution

**Path Parameters**:
- `institution_id` (string, required) — Institution ID

**Query Parameters**: None

**Response** (200 OK):
```json
[
  {
    "proof_id": "PL-2026-00123",
    "institution": {...},
    "instruction": {...},
    "content_hash": "abc123...",
    "signature": "Base64...",
    "status": "ACTIVE",
    "created_at": "2026-08-18T08:00:00Z",
    "expires_at": "2026-08-20T18:00:00Z"
  }
]
```

**Errors**:
- `404 Not Found` — Institution not found

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Status | Meaning | Example |
|---|---|---|
| `200` | Success | Verification completed |
| `201` | Created | ProofLink created |
| `400` | Bad Request | Missing required field |
| `404` | Not Found | ProofLink or Institution doesn't exist |
| `500` | Server Error | Database or signing error |

---

## Cryptographic Details

### Ed25519 Signatures

All ProofLinks are digitally signed using Ed25519 (RFC 8032):

- **Algorithm**: Ed25519
- **Key Size**: 256 bits (32 bytes)
- **Signature Size**: 512 bits (64 bytes)
- **Encoding**: Base64 for API transport
- **Properties**: Unforgeable, deterministic

### SHA-256 Content Hashing

All instructions are hashed using SHA-256:

- **Algorithm**: SHA-256 (FIPS 180-4)
- **Hash Size**: 256 bits (32 bytes)
- **Output**: 64-character hexadecimal string
- **Properties**: Collision-resistant, tamper-proof

### Canonical JSON Representation

Instructions are canonicalized before signing/hashing:

1. All keys are sorted alphabetically
2. No whitespace (compact separators)
3. No Unicode escaping (UTF-8 native)
4. ISO 8601 timestamps (YYYY-MM-DDTHH:MM:SSZ)

**Example**:
```json
{"action":"PAYMENT","amount":80000.0,"currency":"INR","expires_at":"2026-08-20T18:00:00Z","institution_id":"POLICE-MP-001","issued_at":"2026-08-18T08:00:00Z","proof_id":"PL-2026-00123","purpose":"CASE_SETTLEMENT","recipient":"XXXX1234","reference_id":"CASE-2026-00123"}
```

---

## Rate Limiting

Current version has no rate limiting. Recommended:

- Production: Implement 100-1000 requests/minute per IP
- Use API Gateway or middleware for enforcement

---

## CORS

By default, CORS is enabled for all origins (`*`). In production, configure `CORS_ORIGINS` in `.env`:

```
CORS_ORIGINS=["https://frontend.example.com", "https://app.example.com"]
```

---

## Demo Institutions

The following institutions are pre-seeded with Ed25519 keypairs:

| Institution ID | Name | Type |
|---|---|---|
| `POLICE-MP-001` | Madhya Pradesh Police Department | POLICE |
| `SBI-HQ-001` | State Bank of India - Fraud Prevention Unit | BANK |
| `TRAI-GOV-001` | Telecom Regulatory Authority of India | GOVERNMENT |
| `CBI-HQ-001` | Central Bureau of Investigation | POLICE |
| `HDFC-SEC-001` | HDFC Bank Security Operations | BANK |

---

## Examples

### Example 1: Create and Verify a ProofLink

```bash
# Step 1: Create ProofLink
curl -X POST http://localhost:8000/api/v1/prooflinks \
  -H "Content-Type: application/json" \
  -d '{
    "institution_id": "POLICE-MP-001",
    "action": "PAYMENT",
    "amount": 80000,
    "currency": "INR",
    "recipient": "XXXX1234",
    "purpose": "CASE_SETTLEMENT",
    "reference_id": "CASE-2026-00123",
    "expires_at": "2026-08-20T18:00:00Z"
  }'

# Response:
# {
#   "proof_id": "PL-2026-00123",
#   "status": "ACTIVE",
#   "signature_status": "SIGNED"
# }

# Step 2: Verify ProofLink
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"proof_id": "PL-2026-00123"}'

# Response:
# {
#   "status": "VERIFIED",
#   "proof_id": "PL-2026-00123",
#   "checks": {
#     "exists": true,
#     "institution_recognized": true,
#     "signature_valid": true,
#     "hash_valid": true,
#     "amount_match": true,
#     "recipient_match": true,
#     "not_expired": true,
#     "not_revoked": true
#   },
#   ...
# }
```

### Example 2: Revoke a ProofLink

```bash
curl -X POST http://localhost:8000/api/v1/prooflinks/PL-2026-00123/revoke \
  -H "Content-Type: application/json" \
  -d '{"reason": "Instruction cancelled by department"}'

# Response:
# {
#   "proof_id": "PL-2026-00123",
#   "status": "REVOKED"
# }
```

### Example 3: List Institutions

```bash
curl -X GET http://localhost:8000/api/v1/institutions

# Response:
# [
#   {
#     "institution_id": "POLICE-MP-001",
#     "name": "Madhya Pradesh Police Department",
#     "type": "POLICE",
#     "public_key": "...",
#     "status": "ACTIVE"
#   },
#   ...
# ]
```

---

## Changelog

### Version 1.0.0 (2026-08-18)

- Initial release
- 8 API endpoints
- Full Ed25519 and SHA-256 cryptographic support
- PostgreSQL and SQLite support
- 100% test coverage (20 tests)
- Complete OpenAPI documentation

---

## Support

For questions or issues, please refer to the main README.md or open an issue in the repository.
