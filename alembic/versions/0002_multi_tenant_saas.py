"""multi tenant saas migration

Revision ID: 0002_multi_tenant_saas
Revises: 0001_initial
Create Date: 2026-08-18 23:50:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '0002_multi_tenant_saas'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='starter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tenants_id', 'tenants', ['id'], unique=False)
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)

    # Insert default tenant for any existing data
    op.execute("INSERT INTO tenants (id, name, slug, plan, is_active) VALUES (1, 'Default Workspace', 'default-workspace', 'starter', true) ON CONFLICT DO NOTHING;")
    op.execute("SELECT setval('tenants_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tenants));")

    # 2. Update users table
    op.add_column('users', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='admin'))
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'], unique=False)

    # 3. Update documents table
    op.add_column('documents', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, server_default='1'))
    op.add_column('documents', sa.Column('filename', sa.String(length=255), nullable=False, server_default='document.txt'))
    op.add_column('documents', sa.Column('original_filename', sa.String(length=255), nullable=False, server_default='document.txt'))
    op.add_column('documents', sa.Column('file_path', sa.String(length=500), nullable=False, server_default=''))
    op.add_column('documents', sa.Column('file_type', sa.String(length=50), nullable=False, server_default='text/plain'))
    op.add_column('documents', sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('documents', sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('documents', sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'))
    op.add_column('documents', sa.Column('error_message', sa.String(length=500), nullable=True))
    op.create_index('ix_documents_tenant_id', 'documents', ['tenant_id'], unique=False)

    # Drop old unused columns if present
    try:
        op.drop_column('documents', 'title')
    except Exception:
        pass
    try:
        op.drop_column('documents', 'content')
    except Exception:
        pass
    try:
        op.drop_column('documents', 'updated_at')
    except Exception:
        pass

    # 4. Update conversations table
    op.add_column('conversations', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, server_default='1'))
    op.create_index('ix_conversations_tenant_id', 'conversations', ['tenant_id'], unique=False)

    # 5. Update messages table
    op.add_column('messages', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, server_default='1'))
    op.add_column('messages', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
    op.add_column('messages', sa.Column('citations', sa.Text(), nullable=True))
    op.add_column('messages', sa.Column('latency_ms', sa.Integer(), nullable=True))
    op.alter_column('messages', 'sender_id', existing_type=sa.Integer(), nullable=True)
    op.create_index('ix_messages_tenant_id', 'messages', ['tenant_id'], unique=False)
    op.create_index('ix_messages_role', 'messages', ['role'], unique=False)

    # 6. Update tickets table
    op.add_column('tickets', sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, server_default='1'))
    op.add_column('tickets', sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True))
    op.add_column('tickets', sa.Column('priority', sa.String(length=50), nullable=False, server_default='medium'))
    op.create_index('ix_tickets_tenant_id', 'tickets', ['tenant_id'], unique=False)
    op.create_index('ix_tickets_priority', 'tickets', ['priority'], unique=False)
    op.create_index('ix_tickets_conversation_id', 'tickets', ['conversation_id'], unique=False)


def downgrade():
    op.drop_index('ix_tickets_conversation_id', table_name='tickets')
    op.drop_index('ix_tickets_priority', table_name='tickets')
    op.drop_index('ix_tickets_tenant_id', table_name='tickets')
    op.drop_column('tickets', 'priority')
    op.drop_column('tickets', 'conversation_id')
    op.drop_column('tickets', 'tenant_id')

    op.drop_index('ix_messages_role', table_name='messages')
    op.drop_index('ix_messages_tenant_id', table_name='messages')
    op.drop_column('messages', 'latency_ms')
    op.drop_column('messages', 'citations')
    op.drop_column('messages', 'role')
    op.drop_column('messages', 'tenant_id')

    op.drop_index('ix_conversations_tenant_id', table_name='conversations')
    op.drop_column('conversations', 'tenant_id')

    op.drop_index('ix_documents_tenant_id', table_name='documents')
    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'status')
    op.drop_column('documents', 'chunk_count')
    op.drop_column('documents', 'file_size')
    op.drop_column('documents', 'file_type')
    op.drop_column('documents', 'file_path')
    op.drop_column('documents', 'original_filename')
    op.drop_column('documents', 'filename')
    op.drop_column('documents', 'tenant_id')

    op.drop_index('ix_users_tenant_id', table_name='users')
    op.drop_column('users', 'role')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'tenant_id')

    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_index('ix_tenants_id', table_name='tenants')
    op.drop_table('tenants')
