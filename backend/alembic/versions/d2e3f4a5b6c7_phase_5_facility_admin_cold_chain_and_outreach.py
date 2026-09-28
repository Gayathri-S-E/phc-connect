"""Phase 5: Facility Admin, Cold Chain Monitoring and Outreach Camps

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-09-27 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Cold Chain Equipments Table
    op.create_table(
        'cold_chain_equipments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('equipment_type', sa.String(50), nullable=False),
        sa.Column('serial_number', sa.String(100), unique=True, nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('min_temp_c', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('max_temp_c', sa.Float(), nullable=False, server_default='8.0'),
        sa.Column('current_temp_c', sa.Float(), nullable=True),
        sa.Column('last_logged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_functional', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_temperature_in_range', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_cold_chain_equipments_facility_id', 'cold_chain_equipments', ['facility_id'])
    op.create_index('ix_cold_chain_equipments_serial_number', 'cold_chain_equipments', ['serial_number'])

    # 2. Cold Chain Logs Table
    op.create_table(
        'cold_chain_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('equipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cold_chain_equipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recorded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('temperature_c', sa.Float(), nullable=False),
        sa.Column('is_excursion', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('excursion_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_cold_chain_logs_equipment_id', 'cold_chain_logs', ['equipment_id'])

    # 3. Outreach Camps Table
    op.create_table(
        'outreach_camps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('camp_name', sa.String(200), nullable=False),
        sa.Column('target_village', sa.String(100), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('supervisor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='SCHEDULED'),
        sa.Column('target_beneficiaries', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('actual_beneficiaries_served', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_outreach_camps_facility_id', 'outreach_camps', ['facility_id'])
    op.create_index('ix_outreach_camps_scheduled_date', 'outreach_camps', ['scheduled_date'])


def downgrade() -> None:
    op.drop_index('ix_outreach_camps_scheduled_date', table_name='outreach_camps')
    op.drop_index('ix_outreach_camps_facility_id', table_name='outreach_camps')
    op.drop_table('outreach_camps')

    op.drop_index('ix_cold_chain_logs_equipment_id', table_name='cold_chain_logs')
    op.drop_table('cold_chain_logs')

    op.drop_index('ix_cold_chain_equipments_serial_number', table_name='cold_chain_equipments')
    op.drop_index('ix_cold_chain_equipments_facility_id', table_name='cold_chain_equipments')
    op.drop_table('cold_chain_equipments')
