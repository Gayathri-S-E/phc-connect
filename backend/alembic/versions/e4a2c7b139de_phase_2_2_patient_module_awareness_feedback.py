"""Phase 2.2: Patient Module, Awareness Slides, Feedback & Complaints, Notifications

Revision ID: e4a2c7b139de
Revises: 93a1c4b72ef1
Create Date: 2026-09-27 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4a2c7b139de'
down_revision: Union[str, None] = '93a1c4b72ef1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. New Columns on Patients
    op.add_column('patients', sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('patients', sa.Column('chronic_conditions', sa.Text(), nullable=True))
    op.add_column('patients', sa.Column('allergies', sa.Text(), nullable=True))

    # 2. New Columns on Appointments
    op.add_column('appointments', sa.Column('token_number', sa.Integer(), nullable=True))
    op.add_column('appointments', sa.Column('priority', sa.String(20), nullable=False, server_default='ROUTINE'))
    op.add_column('appointments', sa.Column('time_slot', sa.String(50), nullable=True))
    op.create_index('ix_appointments_token_number', 'appointments', ['token_number'])

    # 3. Create ComplaintStatus Enum & Feedback Complaints Table
    complaint_status_enum = postgresql.ENUM('SUBMITTED', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED', name='complaint_status_enum', create_type=True)
    complaint_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'feedback_complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tracking_number', sa.String(50), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('SUBMITTED', 'UNDER_REVIEW', 'RESOLVED', 'REJECTED', name='complaint_status_enum'), nullable=False, server_default='SUBMITTED'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_feedback_complaints_tracking_number', 'feedback_complaints', ['tracking_number'], unique=True)
    op.create_index('ix_feedback_complaints_patient_id', 'feedback_complaints', ['patient_id'])

    # 4. Patient Notifications Table
    op.create_table(
        'patient_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title_en', sa.String(200), nullable=False),
        sa.Column('title_ta', sa.String(200), nullable=False),
        sa.Column('message_en', sa.Text(), nullable=False),
        sa.Column('message_ta', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False, server_default='INFO'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reference_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_patient_notifications_patient_id', 'patient_notifications', ['patient_id'])

    # 5. Health Awareness Slides Table
    op.create_table(
        'health_awareness_slides',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title_en', sa.String(200), nullable=False),
        sa.Column('title_ta', sa.String(200), nullable=False),
        sa.Column('tip_en', sa.Text(), nullable=False),
        sa.Column('tip_ta', sa.Text(), nullable=False),
        sa.Column('motivation_en', sa.Text(), nullable=False),
        sa.Column('motivation_ta', sa.Text(), nullable=False),
        sa.Column('action_en', sa.Text(), nullable=False),
        sa.Column('action_ta', sa.Text(), nullable=False),
        sa.Column('image_key', sa.String(100), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )


def downgrade() -> None:
    op.drop_table('health_awareness_slides')
    op.drop_table('patient_notifications')
    op.drop_table('feedback_complaints')
    op.execute('DROP TYPE IF EXISTS complaint_status_enum')
    op.drop_index('ix_appointments_token_number', table_name='appointments')
    op.drop_column('appointments', 'time_slot')
    op.drop_column('appointments', 'priority')
    op.drop_column('appointments', 'token_number')
    op.drop_column('patients', 'allergies')
    op.drop_column('patients', 'chronic_conditions')
    op.drop_column('patients', 'preferred_language')
