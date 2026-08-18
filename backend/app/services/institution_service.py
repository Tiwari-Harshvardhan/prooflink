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

def register_institution_key(institution_id: str, private_key: ed25519.Ed25519PrivateKey) -> str:
    """Store private key in secure keystore and return its base64 public key."""
    _INSTITUTION_KEY_STORE[institution_id] = private_key
    return export_public_key_b64(private_key.public_key())

def get_institution_private_key(institution_id: str) -> Optional[ed25519.Ed25519PrivateKey]:
    """Retrieve an institution's private key for signing."""
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
        existing = db.query(Institution).filter(Institution.id == inst_id).first()
        
        if not existing:
            # Generate new keypair
            priv_key, pub_key = generate_keypair()
            pub_b64 = export_public_key_b64(pub_key)
            register_institution_key(inst_id, priv_key)

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
            # If institution exists in DB but keystore doesn't have private key (e.g. reload),
            # check if we can assign or keep a keypair in memory.
            if inst_id not in _INSTITUTION_KEY_STORE:
                priv_key, pub_key = generate_keypair()
                register_institution_key(inst_id, priv_key)
                existing.public_key = export_public_key_b64(pub_key)
                db.commit()
