"""
Teleportation-Based Quantum Digital Signature (QDS) Prototype/Simulation
=========================================================================

IMPORTANT DISCLAIMER
--------------------
This module is a PROTOTYPE/SIMULATION of a teleportation-based QDS workflow,
created for the Smart India Hackathon (SIH) demonstration. It is NOT a formally
proven production QDS protocol, and it does NOT claim to provide information-
theoretic security guarantees equivalent to BB84 or other established quantum
cryptographic schemes.

What this prototype DOES demonstrate:
  - Preparation of the six single-qubit Pauli eigenstates (Z, X, Y bases)
  - Bell-pair (|Phi+>) generation via Hadamard + CNOT
  - Standard single-qubit quantum teleportation circuit
  - Pauli X/Z correction based on classical measurement bits (using if_test)
  - Projective measurements in X, Y, and Z bases
  - Repeated-shot statistics to compute empirical error rates
  - Statistical threshold-based accept/reject decision
  - Attack simulation: forgery (wrong state), channel manipulation (Pauli noise)

What this prototype does NOT prove:
  - Unconditional security against computationally unbounded adversaries
  - Quantum authentication against adaptive chosen-message attacks
  - Composable security in the universal framework
  - Any claim about a specific published QDS protocol

Protocol identifier: teleportation-qds-simulation-v1

Qiskit version tested: 2.5.2  (qiskit-aer 0.17.2)
Note: c_if() was removed in Qiskit 2.x; this module uses the if_test()
      context manager instead.

References (structural analogy / context only):
  - Bennett & Brassard (1984) - BB84 QKD
  - Boykin & Roychowdhury (2003) - Optimal Encryption of Quantum Bits
  - Standard quantum teleportation (Nielsen & Chuang, Chapter 1)
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

PROTOCOL_VERSION: str = "teleportation-qds-simulation-v1"

# Default number of measurement shots per verification run
DEFAULT_SHOTS: int = 1024

# Default statistical acceptance threshold (prototype demo value).
# error_rate <= THRESHOLD  ->  VERIFIED
# error_rate >  THRESHOLD  ->  FORGERY_SUSPECTED / CHANNEL_ANOMALY
DEFAULT_THRESHOLD: float = 0.10

# Application-level registry of authorized institution signers
_REGISTERED_SIGNERS: set = {
    "POLICE-MP-001",
    "SBI-HQ-001",
    "TRAI-GOV-001",
    "CBI-HQ-001",
    "HDFC-SEC-001",
    "DEMO-GOV-001",
    "DEMO-POLICE-001",
    "POLICE_DEPT_001",
    "REVENUE_DEPT_001",
}



# ---------------------------------------------------------------------------
# Pauli eigenstate definitions
# ---------------------------------------------------------------------------


@dataclass
class PauliState:
    """One of the six single-qubit Pauli eigenstates."""

    label: str           # "0", "1", "+", "-", "+i", "-i"
    basis: str           # "Z", "X", or "Y"
    eigenvalue: int      # +1 or -1
    expected_outcome: str  # "0" or "1" when measured in the *eigenstate* basis


# The six canonical Pauli eigenstates
PAULI_EIGENSTATES: Dict[str, PauliState] = {
    "0":  PauliState(label="0",  basis="Z", eigenvalue=+1, expected_outcome="0"),
    "1":  PauliState(label="1",  basis="Z", eigenvalue=-1, expected_outcome="1"),
    "+":  PauliState(label="+",  basis="X", eigenvalue=+1, expected_outcome="0"),
    "-":  PauliState(label="-",  basis="X", eigenvalue=-1, expected_outcome="1"),
    "+i": PauliState(label="+i", basis="Y", eigenvalue=+1, expected_outcome="0"),
    "-i": PauliState(label="-i", basis="Y", eigenvalue=-1, expected_outcome="1"),
}

_STATE_LABELS: List[str] = list(PAULI_EIGENSTATES.keys())


# ---------------------------------------------------------------------------
# Qiskit backend helper
# ---------------------------------------------------------------------------


def _get_aer_backend():
    """Return a Qiskit Aer AerSimulator instance (qiskit-aer >= 0.12 preferred)."""
    try:
        from qiskit_aer import AerSimulator  # qiskit-aer >= 0.12 package
        return AerSimulator()
    except ImportError:
        from qiskit.providers.aer import AerSimulator  # type: ignore
        return AerSimulator()


def _run_circuit(circuit, shots: int) -> Dict[str, int]:
    """Transpile and execute a Qiskit circuit; return measurement counts."""
    from qiskit import transpile

    backend = _get_aer_backend()
    compiled = transpile(circuit, backend)
    job = backend.run(compiled, shots=shots)
    result = job.result()
    return result.get_counts()


# ---------------------------------------------------------------------------
# State preparation helpers
# ---------------------------------------------------------------------------


def prepare_zero():
    """Prepare |0> (Z-basis +1 eigenstate). Default initial state - no gate."""
    from qiskit import QuantumCircuit
    return QuantumCircuit(1)


def prepare_one():
    """Prepare |1> (Z-basis -1 eigenstate) via X gate."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1)
    qc.x(0)
    return qc


def prepare_plus():
    """Prepare |+> (X-basis +1 eigenstate) via Hadamard."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1)
    qc.h(0)
    return qc


def prepare_minus():
    """Prepare |-> (X-basis -1 eigenstate) via X then Hadamard."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1)
    qc.x(0)
    qc.h(0)
    return qc


def prepare_plus_i():
    """Prepare |+i> (Y-basis +1 eigenstate) via H then S gate."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.s(0)
    return qc


def prepare_minus_i():
    """Prepare |-i> (Y-basis -1 eigenstate) via H then S-dagger."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1)
    qc.h(0)
    qc.sdg(0)
    return qc


# Map state label -> preparation function
_PREPARE_FN = {
    "0":  prepare_zero,
    "1":  prepare_one,
    "+":  prepare_plus,
    "-":  prepare_minus,
    "+i": prepare_plus_i,
    "-i": prepare_minus_i,
}


def prepare_state(label: str):
    """
    Return a single-qubit QuantumCircuit that prepares the named Pauli eigenstate.

    Supported labels: "0", "1", "+", "-", "+i", "-i"

    Raises:
        ValueError: If label is not one of the six Pauli eigenstates.
    """
    if label not in _PREPARE_FN:
        raise ValueError(
            f"Unknown state label '{label}'. Valid labels: {_STATE_LABELS}"
        )
    return _PREPARE_FN[label]()


# ---------------------------------------------------------------------------
# Bell-pair creation
# ---------------------------------------------------------------------------


def create_bell_pair():
    """
    Create the |Phi+> Bell pair on two qubits.

    Circuit:
        |0> ---[H]---[*]---
                     |
        |0> ---------[X]--

    Result: (|00> + |11>) / sqrt(2)

    Returns:
        2-qubit QuantumCircuit with Bell pair on qubits 0 (Alice) and 1 (Bob).
    """
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.h(0)    # Hadamard on Alice's qubit
    qc.cx(0, 1)  # CNOT: control=0, target=1
    return qc


# ---------------------------------------------------------------------------
# Noise injection
# ---------------------------------------------------------------------------


def _inject_noise(qc, qubit: int, noise_type: str) -> None:
    """
    Inject a deterministic Pauli disturbance to simulate channel manipulation.

    Args:
        qc: QuantumCircuit to modify in-place.
        qubit: Target qubit index.
        noise_type: "X", "Z", or "Y".
    """
    t = noise_type.upper()
    if t == "X":
        qc.x(qubit)
    elif t == "Z":
        qc.z(qubit)
    elif t == "Y":
        qc.y(qubit)
    else:
        logger.warning("Unknown noise type '%s'; no disturbance applied.", noise_type)


# ---------------------------------------------------------------------------
# Measurement basis rotation
# ---------------------------------------------------------------------------


def add_measurement_in_basis(qc, qubit: int, cbit: int, basis: str) -> None:
    """
    Append measurement basis-rotation gates followed by a measurement.

    Rotation:
        Z basis: direct measurement
        X basis: H gate then measure
        Y basis: Sdg gate + H gate then measure

    Args:
        qc: QuantumCircuit to modify in-place.
        qubit: Qubit to measure.
        cbit: Classical bit index to store result.
        basis: "X", "Y", or "Z".
    """
    b = basis.upper()
    if b == "X":
        qc.h(qubit)
    elif b == "Y":
        qc.sdg(qubit)
        qc.h(qubit)
    # Z: no rotation needed
    qc.measure(qubit, cbit)


# ---------------------------------------------------------------------------
# Teleportation + verification circuit
# ---------------------------------------------------------------------------


def build_verification_circuit(
    state_label: str,
    measurement_basis: str,
    apply_noise: bool = False,
    noise_type: str = "X",
    forged_label: Optional[str] = None,
):
    """
    Build the full teleportation + projective-measurement verification circuit.

    Qubit layout:
        q[0] = message qubit (prepared in |state_label> or |forged_label>)
        q[1] = Alice's Bell qubit
        q[2] = Bob's Bell qubit (receives teleported state; measured for verification)

    Classical bits:
        c[0] = Bell measurement on q[0]
        c[1] = Bell measurement on q[1]
        c[2] = Verification projective measurement on q[2]

    Teleportation correction table (standard):
        c[1]=0, c[0]=0 -> I   (no correction)
        c[1]=1, c[0]=0 -> X
        c[1]=0, c[0]=1 -> Z
        c[1]=1, c[0]=1 -> XZ

    Uses Qiskit 2.x if_test() context manager (c_if removed in Qiskit 2.0).

    Args:
        state_label: Pauli eigenstate label committed during signing.
        measurement_basis: Projective measurement basis for q[2] ("X", "Y", "Z").
        apply_noise: If True, inject Pauli disturbance on q[2] (channel simulation).
        noise_type: Disturbance type: "X", "Z", or "Y".
        forged_label: If not None, prepare THIS label instead (forgery simulation).

    Returns:
        3-qubit QuantumCircuit with 3 classical bits, ready for simulation.
    """
    from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister

    prepared_label = forged_label if forged_label is not None else state_label

    qr = QuantumRegister(3, "q")
    cr = ClassicalRegister(3, "c")
    qc = QuantumCircuit(qr, cr)

    # Step 1: Prepare message (or forged) state on q[0]
    state_prep = prepare_state(prepared_label)
    qc.compose(state_prep, qubits=[0], inplace=True)

    # Step 2: Create Bell pair on q[1] and q[2]
    qc.h(1)
    qc.cx(1, 2)

    # Step 3: Bell measurement preparation on q[0] and q[1]
    qc.cx(0, 1)
    qc.h(0)

    # Step 4: Measure q[0] -> c[0], q[1] -> c[1]
    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])

    # Step 5: Classical feed-forward Pauli corrections on q[2]
    # Using Qiskit 2.x if_test() context manager
    with qc.if_test((cr[1], 1)):  # c[1] == 1 -> apply X
        qc.x(2)
    with qc.if_test((cr[0], 1)):  # c[0] == 1 -> apply Z
        qc.z(2)

    # Step 6: Optional Pauli channel disturbance on q[2]
    if apply_noise:
        _inject_noise(qc, qubit=2, noise_type=noise_type)

    # Step 7: Projective measurement on q[2] in the committed basis
    add_measurement_in_basis(qc, qubit=2, cbit=2, basis=measurement_basis)

    return qc


# ---------------------------------------------------------------------------
# Shot statistics and threshold
# ---------------------------------------------------------------------------


def calculate_error_rate(
    counts: Dict[str, int], expected_bit: str
) -> Tuple[int, int, float]:
    """
    Compute empirical error rate from Qiskit measurement counts.

    Qiskit encodes bit strings as "c[n-1]...c[1]c[0]" (MSB = highest-index first).
    In our 3-bit register, c[2] is the verification measurement and appears as
    the LEFTMOST character in the count string.

    Args:
        counts: Qiskit counts dict, e.g. {"000": 512, "100": 512}.
        expected_bit: Expected value of c[2] bit: "0" or "1".

    Returns:
        Tuple of (correct_count, incorrect_count, error_rate).
    """
    total = sum(counts.values())
    if total == 0:
        return 0, 0, 1.0

    correct_count = 0
    for bitstring, count in counts.items():
        # Normalize: strip spaces, zero-pad to 3 digits
        bits = bitstring.replace(" ", "").zfill(3)
        # c[2] is the leftmost (MSB) character
        measured_c2 = bits[0]
        if measured_c2 == expected_bit:
            correct_count += count

    incorrect_count = total - correct_count
    error_rate = incorrect_count / total
    return correct_count, incorrect_count, error_rate


def verify_against_threshold(error_rate: float, threshold: float = DEFAULT_THRESHOLD) -> bool:
    """
    Statistical threshold decision for verification.

    Returns:
        True  (VERIFIED)           if error_rate <= threshold
        False (FORGERY_SUSPECTED)  if error_rate >  threshold

    NOTE: The default threshold (0.10) is a prototype demo value.
    It is NOT a universally proven cryptographically secure bound.
    """
    return error_rate <= threshold


# ---------------------------------------------------------------------------
# QDS Signature Record
# ---------------------------------------------------------------------------


@dataclass
class QDSSignatureRecord:
    """
    Quantum Digital Signature metadata record.

    This record is serialized as JSON and stored in the database
    in the existing ProofLink.signature (Text) column.
    It does NOT contain quantum circuit objects - only classical metadata.
    """

    signature_id: str        # Unique identifier for this QDS signature
    protocol: str            # Protocol version string (PROTOCOL_VERSION)
    instruction_id: str      # ProofLink proof_id this signature is bound to
    signer_id: str           # Institution/signer identifier
    state_label: str         # Pauli eigenstate label committed to during signing
    basis: str               # Measurement basis: "X", "Y", or "Z"
    expected_outcome: str    # Expected measurement bit ("0" or "1")
    nonce: str               # 64-char hex nonce for replay protection
    protocol_version: str    # Semantic version of the QDS protocol
    message_fingerprint: str  # SHA-256 hex of canonical instruction (integrity binding)

    def to_json(self) -> str:
        """Serialize to compact, deterministic JSON for database storage."""
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)

    @staticmethod
    def from_json(s: str) -> "QDSSignatureRecord":
        """Deserialize from JSON string."""
        data = json.loads(s)
        return QDSSignatureRecord(**data)

    def is_valid_format(self) -> bool:
        """Basic structural validation of the signature record fields."""
        return (
            bool(self.signature_id)
            and bool(self.nonce)
            and self.state_label in PAULI_EIGENSTATES
            and self.basis in ("X", "Y", "Z")
            and self.expected_outcome in ("0", "1")
            and self.protocol == PROTOCOL_VERSION
        )


# ---------------------------------------------------------------------------
# QDS Verification Result
# ---------------------------------------------------------------------------


@dataclass
class QDSVerificationResult:
    """Structured result from a QDS verification run."""

    status: str           # VERIFIED | FORGERY_SUSPECTED | CHANNEL_ANOMALY |
    #                     # REPLAY_DETECTED | UNAUTHORIZED_SIGNER | INVALID_SIGNATURE_FORMAT
    protocol: str
    basis: str
    shots: int
    correct_count: int
    incorrect_count: int
    error_rate: float
    threshold: float
    state_label: str
    message: str
    attack_type: Optional[str] = None   # None | FORGERY | CHANNEL_MANIPULATION | REPLAY | IMPERSONATION

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dict for serialization."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Signer registry (application-level authorization complement)
# ---------------------------------------------------------------------------


def register_signer(institution_id: str) -> None:
    """Register an institution as an authorized QDS signer."""
    _REGISTERED_SIGNERS.add(institution_id)


def is_registered_signer(institution_id: str) -> bool:
    """Return True if institution_id is a registered authorized signer."""
    return institution_id in _REGISTERED_SIGNERS


# ---------------------------------------------------------------------------
# Nonce management (replay protection)
# Nonce replay-protection store  { nonce_hex: message_fingerprint }
_USED_NONCES: Dict[str, str] = {}


# ---------------------------------------------------------------------------
# Nonce management (replay protection)
# ---------------------------------------------------------------------------


def _generate_nonce() -> str:
    """Generate a 64-hex-char cryptographically random nonce."""
    return secrets.token_hex(32)


def _mark_nonce_used(nonce: str, fingerprint: str = "used") -> None:
    """Consume a nonce bound to its message fingerprint so it cannot be replayed."""
    _USED_NONCES[nonce] = fingerprint or "used"


def _is_nonce_used(nonce: str) -> bool:
    """Return True if this nonce has already been consumed."""
    return nonce in _USED_NONCES


def reset_nonce_store() -> None:
    """Reset the nonce store (for testing purposes only)."""
    _USED_NONCES.clear()


# ---------------------------------------------------------------------------
# Message fingerprint (SHA-256 binding)
# ---------------------------------------------------------------------------


def _compute_fingerprint(canonical_data: Dict[str, Any]) -> str:
    """
    Compute the SHA-256 hex digest of the canonical instruction dict.

    Role in QDS: message fingerprint = deterministic binding of quantum
    signature to the exact instruction content. This is NOT the signature itself.
    """
    raw = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Deterministic state selection
# ---------------------------------------------------------------------------


def _select_state_label(message_fingerprint: str, signer_id: str) -> str:
    """
    Deterministically select a Pauli eigenstate label from fingerprint + signer.

    This ensures both signer and verifier independently derive the same
    state label for a given instruction + institution pair, without
    transmitting the label separately over an insecure channel.
    """
    combined = f"{message_fingerprint}::{signer_id}"
    idx = int(hashlib.sha256(combined.encode("utf-8")).hexdigest(), 16) % len(_STATE_LABELS)
    return _STATE_LABELS[idx]


def _pick_different_label(original_label: str) -> str:
    """Return a different state label (used to simulate a forgery attempt)."""
    for label in _STATE_LABELS:
        if label != original_label:
            return label
    return "1"  # fallback (should never reach here)


# ---------------------------------------------------------------------------
# QDS SIGN function (public API — replaces sign_canonical_instruction)
# ---------------------------------------------------------------------------


def sign_instruction(
    canonical_data: Dict[str, Any],
    institution_id: str,
    proof_id: str,
) -> "QDSSignatureRecord":
    """
    QDS signing function — replaces Ed25519 signing.

    Internal steps:
      1. Compute SHA-256 message fingerprint (deterministic binding)
      2. Select Pauli eigenstate deterministically from fingerprint + signer ID
      3. Look up the eigenstate's basis and expected measurement outcome
      4. Generate cryptographic nonce and unique signature ID
      5. Register institution as an authorized signer (if not already)
      6. Return a QDSSignatureRecord (no Ed25519 is involved)

    The actual quantum circuit simulation happens at VERIFICATION time.
    During signing, we commit to the state_label, basis, nonce, and
    message fingerprint. The verifier reconstructs the teleportation
    circuit and measures to check integrity.

    Args:
        canonical_data: Canonical instruction dict from create_canonical_instruction().
        institution_id: Signing institution identifier.
        proof_id: Unique ProofLink proof_id (instruction binding).

    Returns:
        QDSSignatureRecord — serialized as JSON and stored in ProofLink.signature.
    """
    # Step 1: SHA-256 fingerprint of canonical instruction
    fingerprint = _compute_fingerprint(canonical_data)

    # Step 2: Deterministic Pauli eigenstate selection
    state_label = _select_state_label(fingerprint, institution_id)
    state = PAULI_EIGENSTATES[state_label]

    # Step 3: Nonce and signature ID
    nonce = _generate_nonce()
    sig_id = f"QDS-{secrets.token_hex(8).upper()}"

    # Step 4: Authorize signer
    register_signer(institution_id)

    record = QDSSignatureRecord(
        signature_id=sig_id,
        protocol=PROTOCOL_VERSION,
        instruction_id=proof_id,
        signer_id=institution_id,
        state_label=state_label,
        basis=state.basis,
        expected_outcome=state.expected_outcome,
        nonce=nonce,
        protocol_version="1.0",
        message_fingerprint=fingerprint,
    )

    logger.info(
        "QDS sign: sig_id=%s proof_id=%s signer=%s state=%s basis=%s",
        sig_id, proof_id, institution_id, state_label, state.basis,
    )
    return record


# ---------------------------------------------------------------------------
# QDS VERIFY function (public API — replaces verify_ed25519_signature)
# ---------------------------------------------------------------------------


def verify_instruction(
    canonical_data: Dict[str, Any],
    signature_json: str,
    institution_id: str,
    shots: int = DEFAULT_SHOTS,
    threshold: float = DEFAULT_THRESHOLD,
    # Attack simulation parameters (demo / test only)
    simulate_forgery: bool = False,
    simulate_channel_noise: bool = False,
    channel_noise_type: str = "X",
    allow_reverify: bool = False,
) -> QDSVerificationResult:
    """
    QDS verification function — replaces verify_ed25519_signature.

    Internal steps:
      1.  Deserialize and structurally validate the signature record
      2.  Check authorized signer (impersonation guard)
      3.  Check nonce replay (replay attack guard)
      4.  Recompute and validate message fingerprint binding
      5.  Reconstruct expected state/basis from signature record
      6.  Build teleportation + measurement verification circuit
      7.  Execute circuit via Qiskit Aer (multiple shots)
      8.  Collect and analyse measurement counts
      9.  Calculate empirical error rate
      10. Compare error rate against configured threshold
      11. Consume nonce (post-verification)
      12. Return structured QDSVerificationResult

    Args:
        canonical_data:       Canonical instruction dict (from DB fields).
        signature_json:       JSON string of QDSSignatureRecord (from DB).
        institution_id:       Institution/signer ID.
        shots:                Number of projective measurement shots.
        threshold:            Max acceptable error rate (default 0.10).
        simulate_forgery:     Demo mode: prepare wrong state to fake forgery.
        simulate_channel_noise: Demo mode: inject Pauli disturbance.
        channel_noise_type:   Pauli disturbance type for channel simulation.

    Returns:
        QDSVerificationResult with full quantum measurement statistics.
    """
    # --- Step 1: Deserialize ---
    try:
        record = QDSSignatureRecord.from_json(signature_json)
    except Exception as exc:
        logger.warning("QDS verify: failed to parse signature JSON: %s", exc)
        return QDSVerificationResult(
            status="INVALID_SIGNATURE_FORMAT",
            protocol=PROTOCOL_VERSION,
            basis="?",
            shots=0,
            correct_count=0,
            incorrect_count=0,
            error_rate=1.0,
            threshold=threshold,
            state_label="?",
            message=f"Signature record is malformed or unreadable: {exc}",
        )

    if not record.is_valid_format():
        return QDSVerificationResult(
            status="INVALID_SIGNATURE_FORMAT",
            protocol=PROTOCOL_VERSION,
            basis=record.basis,
            shots=0,
            correct_count=0,
            incorrect_count=0,
            error_rate=1.0,
            threshold=threshold,
            state_label=record.state_label,
            message="Signature record failed structural validation.",
        )

    # --- Step 2: Impersonation guard ---
    if not is_registered_signer(institution_id):
        logger.warning("QDS verify: unregistered signer '%s'", institution_id)
        return QDSVerificationResult(
            status="UNAUTHORIZED_SIGNER",
            protocol=PROTOCOL_VERSION,
            basis=record.basis,
            shots=0,
            correct_count=0,
            incorrect_count=0,
            error_rate=1.0,
            threshold=threshold,
            state_label=record.state_label,
            message=f"Signer '{institution_id}' is not a registered authorized institution.",
            attack_type="IMPERSONATION",
        )

    # --- Step 3 & 4: Message fingerprint binding & Replay attack guard ---
    expected_fp = _compute_fingerprint(canonical_data)

    if _is_nonce_used(record.nonce):
        prior_fingerprint = _USED_NONCES.get(record.nonce)
        # If allow_reverify is False, any second verification of the same nonce is blocked (single-use test)
        # If allow_reverify is True (used for database-backed ProofLinks), allow re-checking the same instruction,
        # but strictly block cross-instruction replay (attaching the same nonce to a different instruction).
        if not allow_reverify or (prior_fingerprint and prior_fingerprint != "used" and prior_fingerprint != expected_fp):
            logger.warning("QDS verify: replay detected for nonce %s...", record.nonce[:12])
            return QDSVerificationResult(
                status="REPLAY_DETECTED",
                protocol=PROTOCOL_VERSION,
                basis=record.basis,
                shots=0,
                correct_count=0,
                incorrect_count=0,
                error_rate=1.0,
                threshold=threshold,
                state_label=record.state_label,
                message="Replay attack detected: this QDS nonce has already been consumed.",
                attack_type="REPLAY",
            )

    if expected_fp != record.message_fingerprint:
        logger.warning("QDS verify: fingerprint mismatch - instruction tampered")
        return QDSVerificationResult(
            status="FORGERY_SUSPECTED",
            protocol=PROTOCOL_VERSION,
            basis=record.basis,
            shots=shots,
            correct_count=0,
            incorrect_count=shots,
            error_rate=1.0,
            threshold=threshold,
            state_label=record.state_label,
            message="Message fingerprint mismatch: instruction data has been tampered with.",
            attack_type="FORGERY",
        )

    # --- Step 5: State preparation plan ---
    actual_state_label = record.state_label
    forged_label: Optional[str] = None
    attack_type: Optional[str] = None

    if simulate_forgery:
        forged_label = _pick_different_label(record.state_label)
        attack_type = "FORGERY"

    if simulate_channel_noise:
        attack_type = attack_type or "CHANNEL_MANIPULATION"

    # --- Steps 6 & 7: Build and run circuit ---
    try:
        circuit = build_verification_circuit(
            state_label=actual_state_label,
            measurement_basis=record.basis,
            apply_noise=simulate_channel_noise,
            noise_type=channel_noise_type,
            forged_label=forged_label,
        )
        counts = _run_circuit(circuit, shots=shots)
    except Exception as exc:
        logger.exception("QDS verify: circuit simulation failed: %s", exc)
        return QDSVerificationResult(
            status="INVALID_SIGNATURE_FORMAT",
            protocol=PROTOCOL_VERSION,
            basis=record.basis,
            shots=0,
            correct_count=0,
            incorrect_count=0,
            error_rate=1.0,
            threshold=threshold,
            state_label=record.state_label,
            message=f"Quantum circuit simulation failed: {exc}",
        )

    # --- Steps 8 & 9: Error rate calculation ---
    correct, incorrect, error_rate = calculate_error_rate(counts, record.expected_outcome)

    # --- Step 10: Threshold decision ---
    is_verified = verify_against_threshold(error_rate, threshold)

    # --- Step 11: Consume nonce ---
    _mark_nonce_used(record.nonce, expected_fp)

    # --- Step 12: Final status ---
    if simulate_channel_noise and not is_verified:
        final_status = "CHANNEL_ANOMALY"
        message = (
            f"Channel manipulation detected. "
            f"Injected noise: {channel_noise_type}. "
            f"Error rate {error_rate:.4f} > threshold {threshold:.2f}."
        )
    elif is_verified:
        final_status = "VERIFIED"
        message = (
            f"Quantum signature verified. "
            f"Protocol: {PROTOCOL_VERSION}. "
            f"Shots: {shots}. "
            f"Error rate {error_rate:.4f} <= threshold {threshold:.2f}."
        )
    else:
        final_status = "FORGERY_SUSPECTED"
        message = (
            f"Quantum signature verification failed. "
            f"Error rate {error_rate:.4f} > threshold {threshold:.2f}. "
            f"Possible state forgery or channel manipulation."
        )

    logger.info(
        "QDS verify: status=%s state=%s basis=%s shots=%d correct=%d incorrect=%d error=%.4f",
        final_status, actual_state_label, record.basis,
        shots, correct, incorrect, error_rate,
    )

    return QDSVerificationResult(
        status=final_status,
        protocol=PROTOCOL_VERSION,
        basis=record.basis,
        shots=shots,
        correct_count=correct,
        incorrect_count=incorrect,
        error_rate=error_rate,
        threshold=threshold,
        state_label=actual_state_label,
        message=message,
        attack_type=attack_type,
    )
