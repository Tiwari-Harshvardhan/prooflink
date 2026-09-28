# QDS Protocol — Teleportation-Based Quantum Digital Signature Prototype

> **IMPORTANT DISCLAIMER**
> This document describes a **PROTOTYPE/SIMULATION** of a teleportation-based
> Quantum Digital Signature (QDS) workflow, implemented for the Smart India
> Hackathon (SIH) 2026 demonstration. It is **NOT** a formally proven production
> QDS protocol and does **NOT** claim to provide information-theoretic security
> guarantees equivalent to BB84, E91, or any formally analyzed QDS scheme.
> All quantum operations are simulated locally via Qiskit Aer.
> No real quantum hardware is required.

---

## Protocol Identifier

```
teleportation-qds-simulation-v1
```

---

## 1. Overview

PROOFLINK's classical Ed25519 signature layer has been replaced with a
teleportation-based QDS prototype/simulation. The **application workflow is
unchanged**: officials create instructions, ProofLinks are generated and sent
to citizens, and citizens verify them via the same API endpoint.

Only the **cryptographic signing and verification internals** have changed:

| Layer | Old (Classical) | New (QDS Prototype) |
|---|---|---|
| Signing algorithm | Ed25519 | Teleportation-QDS simulation |
| Key material | 32-byte Ed25519 keypair | No asymmetric keys — state commitment |
| Signature format | Base64 (88 chars) | JSON metadata record |
| Verification | Elliptic-curve point check | Quantum measurement statistics |
| Tamper detection | Algebraic impossibility | SHA-256 fingerprint + state mismatch |
| Replay protection | None (application-level) | Nonce consumption + application-level |

---

## 2. State Family — Six Pauli Eigenstates

The protocol uses the **six single-qubit Pauli eigenstates** as the message
state family:

| Label | Basis | Eigenvalue | Preparation | Expected Bit |
|-------|-------|-----------|-------------|-------------|
| `0`   | Z     | +1        | `\|0⟩` (default) | `0` |
| `1`   | Z     | -1        | X gate      | `1` |
| `+`   | X     | +1        | H gate      | `0` |
| `-`   | X     | -1        | X → H       | `1` |
| `+i`  | Y     | +1        | H → S       | `0` |
| `-i`  | Y     | -1        | H → S†      | `1` |

**State selection** is deterministic: given the SHA-256 fingerprint of the
canonical instruction and the institution/signer ID, a specific label is
selected via:

```python
index = SHA256(fingerprint + "::" + signer_id)  mod 6
state_label = PAULI_EIGENSTATES[index]
```

This ensures both signer and verifier independently derive the same state
label for a given instruction + institution pair.

---

## 3. Bell Pair Generation

A |Φ+⟩ Bell pair is created using the standard Hadamard + CNOT circuit:

```
q[1]:  |0⟩ ──[H]──●──
                   │
q[2]:  |0⟩ ───────⊕──
```

Result state:

```
|Φ+⟩ = (|00⟩ + |11⟩) / √2
```

This entangled pair forms the quantum channel for the teleportation protocol.
- **q[1]** = Alice's Bell qubit (stays at the signer side conceptually)
- **q[2]** = Bob's Bell qubit (travels to the verifier side conceptually)

---

## 4. Quantum Teleportation

Standard single-qubit teleportation transfers the message state from q[0] to
q[2] using the Bell pair as the quantum channel.

**Circuit layout:**

```
q[0]: |ψ⟩ ──────────────⊕──[H]──[M]──╥──────
                         │            ║
q[1]: |0⟩ ──[H]──●──────●────────────╫──[M]─
                  │                   ║  ║
q[2]: |0⟩ ────────⊕───────────[X?]─[Z?]─[measure in basis]
                                  ↑    ↑
                              c[1]=1  c[0]=1
```

**Steps:**
1. Prepare message qubit q[0] in the selected Pauli eigenstate
2. Create Bell pair on q[1] and q[2]
3. Bell measurement: CNOT(q[0]→q[1]) + H(q[0]) + measure both
4. Two classical bits c[0] and c[1] are produced
5. Apply Pauli corrections on q[2] based on classical bits

---

## 5. Pauli Corrections

The standard correction table maps measurement outcomes to Pauli gates:

| c[0] (Alice M0) | c[1] (Alice M1) | Correction on Bob's q[2] |
|---|---|---|
| 0 | 0 | I (identity — no correction) |
| 0 | 1 | X gate |
| 1 | 0 | Z gate |
| 1 | 1 | X then Z |

Implementation uses Qiskit 2.x `if_test()` context manager
(note: `c_if()` was removed in Qiskit 2.0):

```python
with qc.if_test((cr[1], 1)):
    qc.x(2)   # X correction
with qc.if_test((cr[0], 1)):
    qc.z(2)   # Z correction
```

After correction, q[2] holds a faithful reconstruction of the original message state.

---

## 6. Measurement Basis

The verifier measures q[2] in the **eigenstate's own basis** to check
teleportation fidelity:

| Basis | Rotation Applied Before Measurement |
|-------|-------------------------------------|
| Z     | None (measure directly)             |
| X     | Hadamard gate                       |
| Y     | S† gate + Hadamard gate             |

For an honest signature (no forgery, no noise), measuring an eigenstate in
its own basis **always** yields the expected bit (0 or 1) with probability 1.

---

## 7. Shot Collection

The verification circuit is run **N shots** (default: 1024):

```python
DEFAULT_SHOTS = 1024
```

Each shot independently executes the teleportation + measurement. The
resulting `counts` dict maps bitstring outcomes to frequency counts.

**Bit-string format (Qiskit convention):** `c[2] c[1] c[0]` — the
verification measurement c[2] appears as the **leftmost character**.

---

## 8. Error Rate Computation

For each shot, the leftmost bit (c[2]) is compared to `expected_outcome`:

```
correct_count   = shots where c[2] == expected_outcome
incorrect_count = shots - correct_count
error_rate      = incorrect_count / shots
```

In an ideal simulation with no noise or forgery, `error_rate = 0.0`.

---

## 9. Statistical Threshold Decision

```python
DEFAULT_THRESHOLD = 0.10

if error_rate <= threshold:
    status = "VERIFIED"
else:
    status = "FORGERY_SUSPECTED"  # or "CHANNEL_ANOMALY"
```

> **Note:** The default threshold of 0.10 is a **prototype demo value**.
> It is NOT a universally proven secure acceptance bound. In a real
> quantum network deployment, the threshold would be derived from
> information-theoretic security proofs for the specific QDS protocol used.

---

## 10. Signature Record (QDSSignatureRecord)

The signing step produces a JSON metadata record stored in the
`ProofLink.signature` database column (Text field — no schema change needed):

```json
{
  "signature_id": "QDS-A1B2C3D4E5F60708",
  "protocol": "teleportation-qds-simulation-v1",
  "instruction_id": "PL-abcd1234token",
  "signer_id": "POLICE-MP-001",
  "state_label": "+",
  "basis": "X",
  "expected_outcome": "0",
  "nonce": "a3f7...64-hex-chars...9c1d",
  "protocol_version": "1.0",
  "message_fingerprint": "sha256hex...64chars...of canonical instruction"
}
```

**Binding:** The `message_fingerprint` is the SHA-256 hash of the canonical
instruction dict. This binds the QDS record to the exact instruction content.

> SHA-256 here = **message fingerprint** (integrity binding)
> NOT = signature (the quantum simulation provides the signature function)

---

## 11. Attack Simulation

The prototype supports four simulated attack modes for demonstration:

### 11.1 Forgery

A forged ProofLink prepares a **different** Pauli eigenstate than the one
committed in the signature record. When measured in the committed basis,
the wrong state produces high error rates:

```
simulate_forgery=True → forged_label = different_state_label
→ measurement distribution changes
→ error_rate ≈ 0.5 to 1.0
→ status = "FORGERY_SUSPECTED"
```

### 11.2 Channel Manipulation (Noise Injection)

A Pauli disturbance gate (X, Z, or Y) is applied to q[2] after the
teleportation correction, simulating a quantum channel attack:

```
simulate_channel_noise=True, channel_noise_type="X"
→ Pauli-X applied to q[2]
→ bit flips measurement outcomes
→ error_rate increases
→ status = "CHANNEL_ANOMALY"
```

Supported disturbance types: X (bit flip), Z (phase flip), Y (bit+phase).

### 11.3 Impersonation

An unregistered institution ID is used as the verifier signer argument.
Detected before running the quantum circuit:

```
institution_id not in _REGISTERED_SIGNERS
→ status = "UNAUTHORIZED_SIGNER"
→ attack_type = "IMPERSONATION"
```

### 11.4 Replay Attack

Each QDS signature record contains a unique 64-hex nonce. The nonce is
consumed (marked as used) after the first successful verification.
A replayed ProofLink presents the same nonce:

```
nonce already in _USED_NONCES
→ status = "REPLAY_DETECTED"
→ attack_type = "REPLAY"
```

---

## 12. Full Verification Status Table

| Status | Description |
|--------|-------------|
| `VERIFIED` | Quantum signature valid; error_rate ≤ threshold |
| `FORGERY_SUSPECTED` | Error rate too high; possible state manipulation |
| `CHANNEL_ANOMALY` | Channel noise injected; error rate exceeds threshold |
| `REPLAY_DETECTED` | Nonce already consumed; replay attack detected |
| `UNAUTHORIZED_SIGNER` | Institution not in authorized signer registry |
| `INVALID_SIGNATURE_FORMAT` | Signature JSON malformed or missing required fields |
| `HASH_MISMATCH` | SHA-256 fingerprint mismatch — content tampered |
| `REVOKED` | Application-level: instruction revoked by issuer |
| `EXPIRED` | Application-level: instruction past expiration timestamp |
| `NOT_FOUND` | Application-level: no ProofLink with this ID |
| `MISMATCH` | Application-level: institution unknown/inactive |

---

## 13. What This Prototype Does NOT Prove

This implementation **deliberately does not claim**:

1. **Unconditional quantum security** — No information-theoretic proof is
   provided that the protocol is secure against computationally unbounded
   adversaries.

2. **Authentication against adaptive chosen-message attacks** — The state
   selection is deterministic, not truly random as required by formal QDS proofs.

3. **Composable security** — The protocol has not been analyzed in any
   universal composability (UC) framework.

4. **Hardware-level quantum properties** — All circuits run on Qiskit Aer
   (classical simulation). No actual quantum entanglement is created.

5. **Forward security** — Replayed signatures are blocked by nonce tracking
   in application memory (not by quantum properties).

6. **Equivalence to any published QDS protocol** — This prototype is a
   didactic demonstration of quantum teleportation concepts applied to
   a signature-like workflow.

---

## 14. File Map

| File | Role |
|------|------|
| `backend/app/crypto/qds.py` | Core QDS protocol: states, teleportation, measurement, sign, verify |
| `backend/app/crypto/signing.py` | Drop-in signing adapter (replaces Ed25519 signing) |
| `backend/app/crypto/verification.py` | Drop-in verification adapter (replaces Ed25519 verification) |
| `backend/app/crypto/keys.py` | Ed25519 shim (Institution.public_key column compatibility only) |
| `backend/app/crypto/hashing.py` | SHA-256 fingerprinting and canonicalization (unchanged) |
| `backend/app/services/verification_service.py` | Updated to call QDS verification; adds quantum stats to response |
| `backend/app/services/prooflink_service.py` | Calls sign_canonical_instruction (unchanged — QDS transparent) |
| `backend/tests/test_qds.py` | Comprehensive QDS unit tests (25 scenarios) |
| `backend/tests/test_crypto.py` | Updated crypto tests adapted for QDS |
| `backend/docs/QDS_PROTOCOL.md` | This document |

---

## 15. Demo Commands

### Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Run tests

```bash
cd backend
pytest -q
```

### Quick QDS smoke test

```python
from app.crypto.qds import sign_instruction, verify_instruction, register_signer, reset_nonce_store

reset_nonce_store()
register_signer("DEMO-INST-001")

canonical = {
    "proof_id": "PL-DEMO-001",
    "institution_id": "DEMO-INST-001",
    "action": "PAYMENT",
    "amount": 5000.0,
    "currency": "INR",
    "recipient": "Harshvardhan Tiwari",
    "purpose": "License fee",
    "reference_id": "abcd#1234",
    "issued_at": "2026-09-01T00:00:00Z",
    "expires_at": "2026-09-30T23:59:59Z",
}

record = sign_instruction(canonical, "DEMO-INST-001", "PL-DEMO-001")
print(f"Signature ID: {record.signature_id}")
print(f"State: |{record.state_label}⟩  Basis: {record.basis}")

result = verify_instruction(canonical, record.to_json(), "DEMO-INST-001")
print(f"Status: {result.status}")
print(f"Shots: {result.shots}  Error rate: {result.error_rate:.4f}")
```

Expected output:
```
Signature ID: QDS-A1B2C3D4...
State: |+⟩  Basis: X
Status: VERIFIED
Shots: 1024  Error rate: 0.0000
```

---

*Document version: 1.0 — September 2026*
*Protocol: teleportation-qds-simulation-v1*
*Qiskit: 2.5.2 | qiskit-aer: 0.17.2*
