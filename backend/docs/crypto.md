# PROOFLINK Cryptographic Architecture

> **Core Principle**: *Don't verify the caller. Verify the instruction.*

This document details the cryptographic design and implementation of PROOFLINK's zero-trust verification system.

---

## Overview

PROOFLINK uses a combination of three well-established cryptographic primitives:

1. **Ed25519 Digital Signatures** — Authority binding and non-repudiation
2. **SHA-256 Hashing** — Content integrity and tamper detection
3. **Canonical JSON** — Deterministic representation and consensus

These combine to provide:
- ✅ **Authenticity**: Only the holder of the private key could have issued this instruction
- ✅ **Integrity**: Any modification to the instruction is detectable
- ✅ **Non-Repudiation**: The issuer cannot deny they signed the instruction
- ✅ **Determinism**: Same instruction always produces identical cryptographic evidence

---

## 1. Ed25519 Digital Signatures

### Overview

Ed25519 is a modern elliptic curve signature scheme specified in RFC 8032. It provides:

- **Security Level**: 128 bits (equivalent to 3072-bit RSA)
- **Signature Size**: 512 bits (64 bytes)
- **Performance**: ~10x faster than RSA
- **Simplicity**: No parameter selection needed (unlike ECDSA)
- **Implementation**: Deterministic (no random number generator required)

### Key Generation

```python
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate a new keypair
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Each key is exactly 32 bytes
print(len(private_key.private_bytes(...)))  # 32
print(len(public_key.public_bytes(...)))    # 32
```

### Key Properties

| Property | Value |
|---|---|
| **Key Size** | 256 bits (32 bytes) |
| **Private Key Format** | 32-byte seed |
| **Public Key Format** | 32-byte compressed point |
| **Signature Size** | 512 bits (64 bytes) |
| **Pre-images** | 2^256 (collision-resistant) |
| **Security Hardness** | ~2^128 operations |

### Key Serialization

For API transport, keys are encoded as Base64:

```python
import base64

# Encode to Base64
pub_b64 = base64.b64encode(public_key_bytes).decode('utf-8')
# Result: "Ql9...3Nw==" (44 characters)

# Decode from Base64
pub_bytes = base64.b64decode(pub_b64)
```

### Threat Model

**What Ed25519 protects against**:
- ✅ Forged signatures (computational infeasibility)
- ✅ Private key recovery (discrete logarithm problem)
- ✅ Public key recovery (one-way function)
- ✅ Signature substitution (deterministic scheme)

**What Ed25519 does NOT protect against**:
- ❌ Loss of private key (user responsibility)
- ❌ Use of weak random number generator (doesn't apply to Ed25519)
- ❌ Implementation side-channels (depends on library)
- ❌ Instruction replay (application responsibility)

---

## 2. SHA-256 Content Hashing

### Overview

SHA-256 is a cryptographic hash function specified in FIPS 180-4:

- **Security Level**: 128 bits (theoretically)
- **Hash Size**: 256 bits (32 bytes)
- **Output Encoding**: 64-character hex string
- **Collision Resistance**: 2^128 hypothetical brute-force attempts
- **Properties**: One-way, deterministic, avalanche effect

### Hashing Process

```python
import hashlib

# Create canonical bytes
data = b"{"proof_id":"PL-2026-00123",...}"

# Calculate SHA-256
digest = hashlib.sha256(data).hexdigest()
# Result: "abc123def456..." (64 hex characters)
```

### Hash Properties

| Property | Value |
|---|---|
| **Input Size** | Unlimited |
| **Output Size** | 256 bits (32 bytes) |
| **Hex String Length** | 64 characters |
| **Output Space** | 2^256 possible values |
| **Collision Probability** | ~2^-128 (negligible) |
| **Preimage Resistance** | 2^256 operations |
| **Second Preimage Resistance** | 2^256 operations |

### Threat Model

**What SHA-256 protects against**:
- ✅ Accidental data corruption (detects any bit change)
- ✅ Intentional tampering (requires 2^256 operations)
- ✅ Collision attacks (2^128 security level)
- ✅ Preimage attacks (2^256 operations)

**What SHA-256 does NOT protect against**:
- ❌ Key leakage (no key used)
- ❌ Timing attacks (constant-time by default)
- ❌ Known-plaintext attacks (not applicable)

---

## 3. Canonical JSON Representation

### Problem: Instruction Determinism

Consider these two JSON representations of the same instruction:

```json
// Representation 1: Compact
{"action":"PAYMENT","amount":80000.0,"currency":"INR"}

// Representation 2: Pretty-printed
{
  "action": "PAYMENT",
  "amount": 80000.0,
  "currency": "INR"
}

// Representation 3: Different key order
{"currency":"INR","action":"PAYMENT","amount":80000.0}
```

These represent identical data but produce **different byte sequences**. If we sign/hash each representation differently, verification fails!

### Solution: Canonicalization

Canonicalization converts all representations to a **single, deterministic byte sequence**:

```python
def canonicalize(obj):
    """Convert to deterministic JSON."""
    return json.dumps(obj, 
                      sort_keys=True,           # Sort keys
                      separators=(',', ':'),    # Compact
                      ensure_ascii=False)       # UTF-8 native

# All three representations above become:
# {"action":"PAYMENT","amount":80000.0,"currency":"INR"}
```

### Canonicalization Rules

1. **Sort Keys Alphabetically**: Ensures consistent key order
   ```
   {"currency":"INR","action":"PAYMENT"} 
   →
   {"action":"PAYMENT","currency":"INR"}
   ```

2. **Compact Separators**: No whitespace
   ```
   { "key" : "value" }
   →
   {"key":"value"}
   ```

3. **UTF-8 Encoding**: No Unicode escaping
   ```
   {"name": "Madhya Pradesh"}  ✓ (UTF-8 native)
   {"name": "Madhya\\u0020Pradesh"}  ✗ (escaped)
   ```

4. **No Trailing Commas**: Strict JSON
   ```
   {"a":1,"b":2}  ✓
   {"a":1,"b":2,}  ✗
   ```

5. **ISO 8601 Timestamps**: Standard format
   ```
   "2026-08-18T08:00:00Z"  ✓
   "2026-08-18 08:00:00"   ✗
   ```

### PROOFLINK Canonical Form

```python
canonical_instruction = {
    "action": "PAYMENT",           # Uppercase
    "amount": 80000.0,             # Float
    "currency": "INR",             # Uppercase
    "expires_at": "2026-08-20T18:00:00Z",  # ISO 8601 UTC
    "institution_id": "POLICE-MP-001",
    "issued_at": "2026-08-18T08:00:00Z",   # ISO 8601 UTC
    "proof_id": "PL-2026-00123",
    "purpose": "CASE_SETTLEMENT",
    "recipient": "XXXX1234",
    "reference_id": "CASE-2026-00123"
}
```

When canonicalized (sorted keys, compact JSON):

```
{"action":"PAYMENT","amount":80000.0,"currency":"INR","expires_at":"2026-08-20T18:00:00Z","institution_id":"POLICE-MP-001","issued_at":"2026-08-18T08:00:00Z","proof_id":"PL-2026-00123","purpose":"CASE_SETTLEMENT","recipient":"XXXX1234","reference_id":"CASE-2026-00123"}
```

---

## 4. Complete Cryptographic Workflow

### 4.1 Instruction Issuance (Institution Side)

```
Input: Instruction Parameters
├─ institution_id = "POLICE-MP-001"
├─ action = "PAYMENT"
├─ amount = 80000
├─ currency = "INR"
├─ recipient = "XXXX1234"
├─ purpose = "CASE_SETTLEMENT"
├─ reference_id = "CASE-2026-00123"
├─ issued_at = 2026-08-18T08:00:00Z
└─ expires_at = 2026-08-20T18:00:00Z

Step 1: Create canonical instruction
└─ Construct dictionary with sorted keys
└─ Result: canonical_dict = {...}

Step 2: Calculate content hash
├─ Canonicalize to JSON bytes
├─ SHA-256(canonical_bytes)
└─ Result: content_hash = "abc123def456..." (64 hex chars)

Step 3: Load institution private key
├─ Retrieve from secure keystore
└─ Result: private_key = Ed25519PrivateKey(...)

Step 4: Sign canonical instruction
├─ Message = canonical_json_bytes
├─ Ed25519.sign(message, private_key)
└─ Result: signature = Base64("...") (88 chars)

Step 5: Store in database
└─ ProofLink record:
   ├─ proof_id
   ├─ institution_id
   ├─ [instruction fields]
   ├─ content_hash
   ├─ signature
   ├─ status
   ├─ created_at
   └─ expires_at

Output: proof_id + signature_status
```

### 4.2 Instruction Verification (Citizen/Verifier Side)

```
Input: proof_id

Step 1: Query database
└─ Retrieve ProofLink record

Step 2: Load institution public key
├─ Retrieve Institution record
└─ Extract public_key_b64

Step 3: Reconstruct canonical instruction
├─ Construct dictionary from stored fields
├─ Sort keys and canonicalize
└─ Result: canonical_dict (same as issuance)

Step 4: Recalculate content hash
├─ SHA-256(canonical_bytes)
└─ Result: recalculated_hash

Step 5: Compare hashes (constant-time)
├─ Stored hash vs. recalculated hash
└─ If mismatch → HASH_MISMATCH

Step 6: Reconstruct message bytes
└─ canonical_json_bytes

Step 7: Verify Ed25519 signature
├─ Message = canonical_json_bytes
├─ Signature = stored_signature_b64
├─ Public key = public_key_b64
├─ Ed25519.verify(message, signature, public_key)
└─ If verification fails → INVALID_SIGNATURE

Step 8: Check revocation status
└─ Query Revocation table
└─ If revoked → REVOKED

Step 9: Check expiration
├─ now() > expires_at?
└─ If expired → EXPIRED

Step 10: Validate fields
├─ amount >= 0?
├─ recipient non-empty?
└─ If fails → MISMATCH

Step 11: Consistency checks
└─ All fields match canonical form

Step 12: Return VERIFIED

Output: VerifyResponse with all checks
```

---

## 5. Security Analysis

### 5.1 Threat: Signature Forgery

**Threat**: Attacker creates a valid signature without the private key

**PROOFLINK Protection**:
- Ed25519 provides 128-bit security level
- Forging requires ~2^128 operations (infeasible)
- No known attacks faster than brute force

**Mitigation**: Use recommended key sizes (32 bytes for Ed25519)

### 5.2 Threat: Hash Collision

**Threat**: Attacker finds two different instructions with identical hash

**PROOFLINK Protection**:
- SHA-256 has 256-bit output space (2^256 possible values)
- Collision requires ~2^128 operations (birthday attack, infeasible)
- No collisions found for SHA-256

**Mitigation**: No changes needed; SHA-256 is cryptographically sound

### 5.3 Threat: Instruction Tampering

**Threat**: Attacker modifies an instruction's data (amount, recipient, etc.)

**PROOFLINK Protection**:
1. Hash detects any bit change
2. Signature verification fails against tampered hash
3. Constant-time comparison prevents timing attacks

**Mitigation**: Hash comparison uses `hmac.compare_digest()`

### 5.4 Threat: Private Key Loss

**Threat**: Private key is stolen, leaked, or lost

**PROOFLINK Protection**:
- Private keys are NOT stored in database (only in memory)
- Private keys are NOT returned in any API response
- Private keys should be stored in HSM or KMS

**Mitigation**: Enterprise deployment should use AWS KMS, HashiCorp Vault, or HSM

### 5.5 Threat: Instruction Replay

**Threat**: Attacker captures a valid ProofLink and submits it again

**PROOFLINK Protection**:
- ProofLinks are stored in database with created_at and expires_at
- Same proof_id can only exist once
- Frontend/application should validate timestamps

**Mitigation**: Application layer should check creation time and context

### 5.6 Threat: Timing Attack on Hash Comparison

**Threat**: Attacker measures comparison time to infer hash prefix

**PROOFLINK Protection**:
- Hash comparison uses `hmac.compare_digest()` (constant-time)
- All bytes compared, not short-circuited on first mismatch

**Mitigation**: Never use `==` for cryptographic comparisons; use `hmac.compare_digest()`

### 5.7 Threat: Canonical Form Bypass

**Threat**: Attacker creates two representations of same instruction that produce different hashes

**PROOFLINK Protection**:
- Canonical JSON with sorted keys and compact representation
- UTF-8 native (no Unicode escaping)
- Deterministic timestamp formatting
- Recursive sorting for nested objects

**Mitigation**: Strictly enforce canonicalization rules in code

---

## 6. Key Management

### Generation

```python
from app.crypto.keys import generate_keypair, export_public_key_b64, export_private_key_b64

# Generate new keypair
priv_key, pub_key = generate_keypair()

# Export to Base64
pub_b64 = export_public_key_b64(pub_key)
priv_b64 = export_private_key_b64(priv_key)

# Store public_b64 in Institution.public_key
# Store priv_b64 in secure keystore (never in DB)
```

### Storage

**Public Keys** (can be public):
- Stored in `institutions.public_key` column
- Returned in API responses
- Used for verification

**Private Keys** (must be secret):
- ❌ NOT stored in database
- ✅ Stored in in-memory Python dictionary (for demo)
- ✅ In production: AWS KMS, HashiCorp Vault, HSM
- ❌ Never logged, never returned in API
- ✅ Always sanitized with `sanitize_institution_data()`

### Rotation

To rotate keys:

1. Generate new Ed25519 keypair
2. Update `institutions.public_key` with new public key
3. Update keystore with new private key
4. Old signatures remain valid (verification uses current public key)
5. New instructions use new private key

---

## 7. Implementation Details

### Libraries Used

- **cryptography** >= 42.0.5 — Ed25519, SHA-256, serialization
- **hashlib** — Built-in SHA-256 (via `cryptography`)
- **json** — Canonical JSON (built-in)
- **base64** — Key/signature encoding (built-in)
- **hmac** — Constant-time comparison (built-in)

### Code Example: Full Lifecycle

```python
from app.crypto import (
    generate_keypair,
    export_public_key_b64,
    create_canonical_instruction,
    calculate_content_hash,
    sign_canonical_instruction,
    verify_ed25519_signature
)

# 1. Institution generates keypair
priv_key, pub_key = generate_keypair()
pub_b64 = export_public_key_b64(pub_key)

# 2. Create instruction
canonical = create_canonical_instruction(
    proof_id="PL-2026-00123",
    institution_id="POLICE-MP-001",
    action="PAYMENT",
    amount=80000,
    currency="INR",
    recipient="XXXX1234",
    purpose="CASE_SETTLEMENT",
    reference_id="CASE-2026-00123",
    issued_at="2026-08-18T08:00:00Z",
    expires_at="2026-08-20T18:00:00Z"
)

# 3. Hash and sign
content_hash = calculate_content_hash(canonical)
signature = sign_canonical_instruction(priv_key, canonical)

# 4. Store in database
prooflink = ProofLink(
    proof_id="PL-2026-00123",
    institution_id="POLICE-MP-001",
    content_hash=content_hash,
    signature=signature,
    ...
)
db.add(prooflink)

# 5. Verify (citizen side)
is_valid = verify_ed25519_signature(pub_b64, signature, canonical)
# Result: True
```

---

## 8. Security Recommendations

### Development
- ✅ Use built-in `cryptography` library (battle-tested)
- ✅ Never implement crypto from scratch
- ✅ Use Ed25519 (simpler than ECDSA)
- ✅ Use SHA-256 (standard, well-vetted)

### Production
- ✅ Store private keys in HSM or KMS
- ✅ Enable audit logging for all signature operations
- ✅ Use TLS 1.2+ for API transport
- ✅ Implement rate limiting to prevent brute-force
- ✅ Monitor for repeated verification failures (possible attacks)

### Testing
- ✅ Unit tests for all crypto functions
- ✅ Test both valid and invalid signatures
- ✅ Test tamper detection (modified amounts, recipients, etc.)
- ✅ Test canonical form consistency
- ✅ Fuzz test with random inputs

---

## 9. References

- **Ed25519**: RFC 8032 — "Edwards-Curve Digital Signature Algorithm (EdDSA)"
- **SHA-256**: FIPS 180-4 — "Secure Hash Standard (SHS)"
- **JSON Canonicalization**: RFC 7231 (JSON Web Signature)
- **cryptography library**: https://cryptography.io/

---

## 10. FAQ

**Q: Why Ed25519 and not RSA?**  
A: Ed25519 is more secure per bit, faster, and simpler (no padding schemes like PKCS#1 v1.5).

**Q: Why SHA-256 and not SHA-1?**  
A: SHA-1 is cryptographically broken. SHA-256 has 128-bit security level.

**Q: What if the private key is lost?**  
A: All future signatures fail. Historical signatures remain valid. In production, use key recovery systems (KMS).

**Q: Can the same instruction have two valid signatures?**  
A: No. Ed25519 produces one canonical signature for a given message and private key.

**Q: What prevents instruction replay?**  
A: Application layer (checking timestamps and context). PROOFLINK stores creation time.

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-18  
**Author**: PROOFLINK Team
