"""fix timestamp defaults and backfill

Revision ID: 0003_fix_timestamp_defaults
Revises: 0002_multi_tenant_saas
Create Date: 2026-09-18 23:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0003_fix_timestamp_defaults'
down_revision = '0002_multi_tenant_saas'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Backfill any existing NULL timestamps in PostgreSQL
    op.execute("UPDATE conversations SET updated_at = COALESCE(updated_at, created_at, NOW()), created_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL OR created_at IS NULL;")
    op.execute("UPDATE tickets SET updated_at = COALESCE(updated_at, created_at, NOW()), created_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL OR created_at IS NULL;")
    op.execute("UPDATE messages SET created_at = COALESCE(created_at, NOW()) WHERE created_at IS NULL;")
    op.execute("UPDATE documents SET created_at = COALESCE(created_at, NOW()) WHERE created_at IS NULL;")

    # 2. Alter column server_default to now() so all future raw inserts also receive a timestamp
    op.alter_column('conversations', 'created_at', server_default=sa.text('now()'), nullable=False)
    op.alter_column('conversations', 'updated_at', server_default=sa.text('now()'), nullable=False)
    op.alter_column('tickets', 'created_at', server_default=sa.text('now()'), nullable=False)
    op.alter_column('tickets', 'updated_at', server_default=sa.text('now()'), nullable=False)
    op.alter_column('messages', 'created_at', server_default=sa.text('now()'), nullable=False)


def downgrade():
    pass
