"""initial schema: institutions, prooflinks, revocations

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


institution_type = sa.Enum(
    "POLICE", "BANK", "GOVERNMENT", "COURT", "TELECOM", "OTHER", name="institution_type"
)
institution_status = sa.Enum("ACTIVE", "SUSPENDED", name="institution_status")
prooflink_status = sa.Enum("ACTIVE", "EXPIRED", "REVOKED", name="prooflink_status")


def upgrade() -> None:
    bind = op.get_bind()
    institution_type.create(bind, checkfirst=True)
    institution_status.create(bind, checkfirst=True)
    prooflink_status.create(bind, checkfirst=True)

    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("institution_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", institution_type, nullable=False),
        # PUBLIC key only — no private key column exists in this schema.
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("status", institution_status, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_institutions_institution_id", "institutions", ["institution_id"])
    op.create_index("ix_institutions_institution_id", "institutions", ["institution_id"])

    op.create_table(
        "prooflinks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("proof_id", sa.String(length=32), nullable=False),
        sa.Column(
            "institution_id",
            sa.String(length=64),
            sa.ForeignKey("institutions.institution_id"),
            nullable=False,
        ),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="INR"),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("reference_id", sa.String(length=128), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("status", prooflink_status, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_prooflinks_proof_id", "prooflinks", ["proof_id"])
    op.create_index("ix_prooflinks_proof_id", "prooflinks", ["proof_id"])
    op.create_index("ix_prooflinks_institution_id", "prooflinks", ["institution_id"])
    op.create_index("ix_prooflinks_status", "prooflinks", ["status"])
    op.create_index("ix_prooflinks_institution_status", "prooflinks", ["institution_id", "status"])

    op.create_table(
        "revocations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "proof_id",
            sa.String(length=32),
            sa.ForeignKey("prooflinks.proof_id"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_by", sa.String(length=255), nullable=False),
    )
    op.create_unique_constraint("uq_revocations_proof_id", "revocations", ["proof_id"])
    op.create_index("ix_revocations_proof_id", "revocations", ["proof_id"])


def downgrade() -> None:
    op.drop_table("revocations")
    op.drop_table("prooflinks")
    op.drop_table("institutions")

    bind = op.get_bind()
    prooflink_status.drop(bind, checkfirst=True)
    institution_status.drop(bind, checkfirst=True)
    institution_type.drop(bind, checkfirst=True)
