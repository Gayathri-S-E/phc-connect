"""Common AI Foundation: conversations, messages and confirmed-action requests

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-09-30 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_ENUM = postgresql.ENUM(
    'PENDING', 'EXECUTING', 'EXECUTED', 'FAILED', 'CANCELLED', 'EXPIRED',
    name='ai_pending_action_status_enum', create_type=False,
)


def upgrade() -> None:
    STATUS_ENUM.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assistant', sa.String(40), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])
    op.create_index('ix_ai_conversations_assistant', 'ai_conversations', ['assistant'])
    op.create_index('ix_ai_conversations_updated_at', 'ai_conversations', ['updated_at'])

    op.create_table(
        'ai_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(12), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])

    op.create_table(
        'ai_pending_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assistant', sa.String(40), nullable=False),
        sa.Column('tool_name', sa.String(80), nullable=False),
        sa.Column('arguments', postgresql.JSONB(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('status', STATUS_ENUM, nullable=False, server_default='PENDING'),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_ai_pending_actions_conversation_id', 'ai_pending_actions', ['conversation_id'])
    op.create_index('ix_ai_pending_actions_user_id', 'ai_pending_actions', ['user_id'])
    op.create_index('ix_ai_pending_actions_status', 'ai_pending_actions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_ai_pending_actions_status', table_name='ai_pending_actions')
    op.drop_index('ix_ai_pending_actions_user_id', table_name='ai_pending_actions')
    op.drop_index('ix_ai_pending_actions_conversation_id', table_name='ai_pending_actions')
    op.drop_table('ai_pending_actions')
    op.drop_index('ix_ai_messages_conversation_id', table_name='ai_messages')
    op.drop_table('ai_messages')
    op.drop_index('ix_ai_conversations_updated_at', table_name='ai_conversations')
    op.drop_index('ix_ai_conversations_assistant', table_name='ai_conversations')
    op.drop_index('ix_ai_conversations_user_id', table_name='ai_conversations')
    op.drop_table('ai_conversations')
    STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
