"""Bed availability: bed_inventory and append-only bed_census_log

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-09-30 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WARD = postgresql.ENUM('GENERAL', 'MATERNITY', 'PAEDIATRIC', 'ISOLATION', 'ICU',
                       name='ward_type_enum', create_type=False)


def upgrade() -> None:
    WARD.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'bed_inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ward_type', WARD, nullable=False),
        sa.Column('total_beds', sa.Integer(), nullable=False),
        sa.Column('occupied_beds', sa.Integer(), nullable=False),
        sa.Column('last_updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('facility_id', 'ward_type', name='uq_bed_inventory_facility_ward'),
        sa.CheckConstraint('total_beds >= 0', name='chk_bed_total_non_negative'),
        sa.CheckConstraint('occupied_beds >= 0', name='chk_bed_occupied_non_negative'),
        sa.CheckConstraint('occupied_beds <= total_beds', name='chk_bed_occupied_lte_total'),
    )
    op.create_index('ix_bed_inventory_facility_id', 'bed_inventory', ['facility_id'])
    op.create_table(
        'bed_census_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ward_type', WARD, nullable=False),
        sa.Column('total_beds', sa.Integer(), nullable=False),
        sa.Column('occupied_beds', sa.Integer(), nullable=False),
        sa.Column('previous_total_beds', sa.Integer(), nullable=True),
        sa.Column('previous_occupied_beds', sa.Integer(), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_bed_census_log_facility_id', 'bed_census_log', ['facility_id'])
    op.create_index('ix_bed_census_log_recorded_at', 'bed_census_log', ['recorded_at'])


def downgrade() -> None:
    op.drop_table('bed_census_log')
    op.drop_table('bed_inventory')
    WARD.drop(op.get_bind(), checkfirst=True)
