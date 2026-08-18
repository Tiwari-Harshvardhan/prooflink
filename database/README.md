# PROOFLINK — Database Layer

PostgreSQL schema for the PROOFLINK registry, owned by the frontend/database
role. This layer does **not** implement Ed25519 signing, SHA-256 hashing, or
verification logic — it only stores the results of those operations,
produced by the backend/crypto layer.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL
```

## Run migrations

```bash
alembic upgrade head
```

## Seed demo data

```bash
python seed.py
```

This creates two institutions and three ProofLinks covering all three
`status` states (`ACTIVE`, `EXPIRED`, `REVOKED`), so the frontend has real
data to render before the backend is wired up. Seeded `signature` and
`content_hash` values are clearly-marked placeholders, not real signatures.

## Schema

| Table          | Purpose                                                        |
|----------------|------------------------------------------------------------------|
| `institutions` | Authorities that can issue instructions. Stores **public** key only. |
| `prooflinks`   | Individual signed instructions, keyed by public `proof_id`.    |
| `revocations`  | One row per revoked ProofLink, with reason and revoker.        |

## Security note

`institutions.public_key` is a public key. No table in this schema stores a
private key — private keys belong entirely to the cryptographic/backend
layer and must never be persisted here or exposed to the frontend.
