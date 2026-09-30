"""Federated forecasting tables (aggregate parameters only)

Revision ID: b9c0d1e2f3a4
Revises: a7b8c9d0e1f2
Create Date: 2026-09-30 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'federated_local_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('state_key', sa.String(100), nullable=False),
        sa.Column('state_label', sa.String(100), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('round_no', sa.Integer(), nullable=False),
        sa.Column('window_days', sa.Integer(), nullable=False),
        sa.Column('n_facilities', sa.Integer(), nullable=False),
        sa.Column('n_samples', sa.Integer(), nullable=False),
        sa.Column('mean_daily_rate', sa.Float(), nullable=False),
        sa.Column('variance', sa.Float(), nullable=False),
        sa.Column('seasonality', sa.JSON(), nullable=False),
        sa.Column('computed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('state_key', 'medication_id', name='uq_fed_local_state_medication'),
    )
    op.create_index('ix_federated_local_updates_state_key', 'federated_local_updates', ['state_key'])
    op.create_index('ix_federated_local_updates_medication_id', 'federated_local_updates', ['medication_id'])

    op.create_table(
        'federated_national_priors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('round_no', sa.Integer(), nullable=False),
        sa.Column('n_states', sa.Integer(), nullable=False),
        sa.Column('n_samples', sa.Integer(), nullable=False),
        sa.Column('mean_daily_rate', sa.Float(), nullable=False),
        sa.Column('variance', sa.Float(), nullable=False),
        sa.Column('seasonality', sa.JSON(), nullable=False),
        sa.Column('contributing_states', sa.JSON(), nullable=False),
        sa.Column('aggregated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('aggregated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_federated_national_priors_medication_id', 'federated_national_priors', ['medication_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_federated_national_priors_medication_id', table_name='federated_national_priors')
    op.drop_table('federated_national_priors')
    op.drop_index('ix_federated_local_updates_medication_id', table_name='federated_local_updates')
    op.drop_index('ix_federated_local_updates_state_key', table_name='federated_local_updates')
    op.drop_table('federated_local_updates')
