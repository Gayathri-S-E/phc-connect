"""Phase 3: Staff Attendance and Triage Vitals

Revision ID: f8b3c9d12a45
Revises: e4a2c7b139de
Create Date: 2026-09-27 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f8b3c9d12a45'
down_revision: Union[str, None] = 'e4a2c7b139de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add triage fields to vitals
    op.add_column('vitals', sa.Column('triage_level', sa.String(20), nullable=True, server_default='ROUTINE'))
    op.add_column('vitals', sa.Column('triage_notes', sa.Text(), nullable=True))

    # 2. Create AttendanceStatus Enum & Staff Attendance Table
    attendance_status_enum = postgresql.ENUM('PRESENT', 'HALF_DAY', 'ON_LEAVE', 'ON_DUTY_CAMP', name='attendance_status_enum', create_type=True)
    # attendance_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'staff_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('check_out_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PRESENT', 'HALF_DAY', 'ON_LEAVE', 'ON_DUTY_CAMP', name='attendance_status_enum'), nullable=False, server_default='PRESENT'),
        sa.Column('shift', sa.String(50), nullable=False, server_default='GENERAL'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_staff_attendance_user_id', 'staff_attendance', ['user_id'])
    op.create_index('ix_staff_attendance_facility_id', 'staff_attendance', ['facility_id'])
    op.create_index('ix_staff_attendance_attendance_date', 'staff_attendance', ['attendance_date'])


def downgrade() -> None:
    op.drop_index('ix_staff_attendance_attendance_date', table_name='staff_attendance')
    op.drop_index('ix_staff_attendance_facility_id', table_name='staff_attendance')
    op.drop_index('ix_staff_attendance_user_id', table_name='staff_attendance')
    op.drop_table('staff_attendance')

    attendance_status_enum = postgresql.ENUM('PRESENT', 'HALF_DAY', 'ON_LEAVE', 'ON_DUTY_CAMP', name='attendance_status_enum')
    attendance_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_column('vitals', 'triage_notes')
    op.drop_column('vitals', 'triage_level')
