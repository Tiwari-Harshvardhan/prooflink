# PROOFLINK — Frontend & Database

This repo covers the **frontend** and **database** layers of PROOFLINK, per
the project specification. Cryptography (Ed25519 signing, SHA-256 hashing,
signature verification) and the FastAPI business logic are owned by the
backend developer and are not implemented here.

```
prooflink/
├── frontend/     React + TypeScript + Vite + Tailwind UI
└── database/     PostgreSQL schema, SQLAlchemy models, Alembic migrations, seed data
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs against in-memory mock data by default (`USE_MOCKS = true` in
`src/services/api.ts`). Every network call lives in that one file — when the
FastAPI backend is ready, set `VITE_API_BASE_URL` (see `.env.example`) and
flip `USE_MOCKS` to `false`. No page or component needs to change.

Pages:

| Route                        | Purpose                       |
|-------------------------------|--------------------------------|
| `/`                           | Home / landing                |
| `/verify`                     | Citizen enters a Proof ID      |
| `/verify/result/:proofId`     | Verification result + checks   |
| `/institution`                | Institution dashboard          |
| `/institution/create`         | Issue a new ProofLink          |
| `/how-it-works`               | Architecture explainer         |

## Database

```bash
cd database
pip install -r requirements.txt
alembic upgrade head
python seed.py
```

See `database/README.md` for schema details.

## Design principle

The frontend never verifies, signs, or asserts anything — it only renders
what the backend returns. `VERIFIED`, `NOT_FOUND`, `MISMATCH`,
`INVALID_SIGNATURE`, `EXPIRED`, and `REVOKED` are the backend's results,
not client-side computations.
