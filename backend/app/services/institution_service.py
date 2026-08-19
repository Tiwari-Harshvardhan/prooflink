"""
Institution Service: Manages registered institutions and secure Ed25519 KeyStore.
"""
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import ed25519
from app.models.institution import Institution
from app.crypto.keys import generate_keypair, export_public_key_b64, export_private_key_b64, load_private_key_b64

# Secure in-memory KeyStore for demo/institution private keys.
# In a full enterprise environment, this connects to HSM / AWS KMS / HashiCorp Vault.
# CRITICAL: Private keys in this store are NEVER sent to the frontend or written to public DB columns.
_INSTITUTION_KEY_STORE: Dict[str, ed25519.Ed25519PrivateKey] = {}

# Demo institutional definitions
DEFAULT_INSTITUTIONS = [
    {
        "id": "POLICE-MP-001",
        "name": "Madhya Pradesh Police Department",
        "type": "POLICE",
        "status": "ACTIVE"
    },
    {
        "id": "SBI-HQ-001",
        "name": "State Bank of India - Fraud Prevention Unit",
        "type": "BANK",
        "status": "ACTIVE"
    },
    {
        "id": "TRAI-GOV-001",
        "name": "Telecom Regulatory Authority of India",
        "type": "GOVERNMENT",
        "status": "ACTIVE"
    },
    {
        "id": "CBI-HQ-001",
        "name": "Central Bureau of Investigation",
        "type": "POLICE",
        "status": "ACTIVE"
    },
    {
        "id": "HDFC-SEC-001",
        "name": "HDFC Bank Security Operations",
        "type": "BANK",
        "status": "ACTIVE"
    }
]

import hashlib

def get_institution_keypair(institution_id: str) -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    """Derive deterministic Ed25519 keypair for an institution (HSM/KMS adapter in production)."""
    seed = hashlib.sha256(f"PROOFLINK_INSTITUTION_ED25519_KEY_{institution_id}".encode("utf-8")).digest()
    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    return priv_key, priv_key.public_key()

def register_institution_key(institution_id: str, private_key: ed25519.Ed25519PrivateKey) -> str:
    """Store private key in secure keystore and return its base64 public key."""
    _INSTITUTION_KEY_STORE[institution_id] = private_key
    return export_public_key_b64(private_key.public_key())

def get_institution_private_key(institution_id: str) -> Optional[ed25519.Ed25519PrivateKey]:
    """Retrieve an institution's private key for signing."""
    if institution_id not in _INSTITUTION_KEY_STORE:
        priv_key, _ = get_institution_keypair(institution_id)
        _INSTITUTION_KEY_STORE[institution_id] = priv_key
    return _INSTITUTION_KEY_STORE.get(institution_id)

def get_institution(db: Session, institution_id: str) -> Optional[Institution]:
    """Fetch an institution by ID from the database."""
    return db.query(Institution).filter(Institution.id == institution_id).first()

def get_all_institutions(db: Session) -> List[Institution]:
    """Fetch all institutions."""
    return db.query(Institution).all()

def seed_default_institutions(db: Session) -> None:
    """Ensure default demo institutions and keys are seeded in DB and KeyStore."""
    for inst_data in DEFAULT_INSTITUTIONS:
        inst_id = inst_data["id"]
        priv_key, pub_key = get_institution_keypair(inst_id)
        pub_b64 = register_institution_key(inst_id, priv_key)
        
        existing = db.query(Institution).filter(Institution.id == inst_id).first()
        if not existing:
            institution = Institution(
                id=inst_id,
                name=inst_data["name"],
                type=inst_data["type"],
                public_key=pub_b64,
                status=inst_data["status"]
            )
            db.add(institution)
            db.commit()
        else:
            if existing.public_key != pub_b64:
                existing.public_key = pub_b64
                db.commit()
