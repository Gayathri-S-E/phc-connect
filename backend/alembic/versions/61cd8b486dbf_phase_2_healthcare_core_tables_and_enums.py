"""Phase 2: Healthcare Core tables and enums

Revision ID: 61cd8b486dbf
Revises: 74749546cd8b
Create Date: 2026-09-27 20:24:54.000853

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '61cd8b486dbf'
down_revision: Union[str, None] = '74749546cd8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Patients
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), unique=True, nullable=True),
        sa.Column('primary_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('patient_identifier', sa.String(50), nullable=False, unique=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(20), nullable=False),
        sa.Column('phone_number', sa.String(50), nullable=False),
        sa.Column('blood_group', sa.String(10), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('emergency_contact_name', sa.String(100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(50), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_patients_patient_identifier', 'patients', ['patient_identifier'])
    op.create_index('ix_patients_phone_number', 'patients', ['phone_number'])
    op.create_index('ix_patients_primary_facility_id', 'patients', ['primary_facility_id'])

    # 2. Appointments
    op.create_table(
        'appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('appointment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'status',
            sa.Enum('SCHEDULED', 'CHECKED_IN', 'IN_CONSULTATION', 'COMPLETED', 'CANCELLED', 'NO_SHOW', name='appointment_status_enum'),
            nullable=False,
            server_default='SCHEDULED',
        ),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
    op.create_index('ix_appointments_facility_id', 'appointments', ['facility_id'])
    op.create_index('ix_appointments_doctor_id', 'appointments', ['doctor_id'])
    op.create_index('ix_appointments_appointment_date', 'appointments', ['appointment_date'])

    # 3. Consultations
    op.create_table(
        'consultations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('appointments.id', ondelete='SET NULL'), unique=True, nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column(
            'status',
            sa.Enum('IN_PROGRESS', 'FINALIZED', 'CANCELLED', name='consultation_status_enum'),
            nullable=False,
            server_default='IN_PROGRESS',
        ),
        sa.Column('triage_vitals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chief_complaint', sa.Text(), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column('examination_findings', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_consultations_patient_id', 'consultations', ['patient_id'])
    op.create_index('ix_consultations_doctor_id', 'consultations', ['doctor_id'])
    op.create_index('ix_consultations_facility_id', 'consultations', ['facility_id'])

    # 4. Diagnoses
    op.create_table(
        'diagnoses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('icd10_code', sa.String(20), nullable=False),
        sa.Column('condition_name', sa.String(255), nullable=False),
        sa.Column(
            'diagnosis_type',
            sa.Enum('PRIMARY', 'SECONDARY', 'PROVISIONAL', name='diagnosis_type_enum'),
            nullable=False,
            server_default='PRIMARY',
        ),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_diagnoses_consultation_id', 'diagnoses', ['consultation_id'])
    op.create_index('ix_diagnoses_patient_id', 'diagnoses', ['patient_id'])
    op.create_index('ix_diagnoses_icd10_code', 'diagnoses', ['icd10_code'])

    # 5. Prescriptions
    op.create_table(
        'prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'ISSUED', 'PARTIALLY_DISPENSED', 'COMPLETED', 'CANCELLED', name='prescription_status_enum'),
            nullable=False,
            server_default='ISSUED',
        ),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_prescriptions_consultation_id', 'prescriptions', ['consultation_id'])
    op.create_index('ix_prescriptions_patient_id', 'prescriptions', ['patient_id'])
    op.create_index('ix_prescriptions_facility_id', 'prescriptions', ['facility_id'])

    # 6. Prescription Items
    op.create_table(
        'prescription_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prescription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('medication_name', sa.String(255), nullable=False),
        sa.Column('medication_code', sa.String(100), nullable=True),
        sa.Column('dosage', sa.String(100), nullable=False),
        sa.Column('frequency', sa.String(100), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('quantity_prescribed', sa.Integer(), nullable=False),
        sa.Column('quantity_dispensed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'DISPENSED', 'CANCELLED', name='prescription_item_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
    )
    op.create_index('ix_prescription_items_prescription_id', 'prescription_items', ['prescription_id'])

    # 7. Lab Orders
    op.create_table(
        'lab_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ordered_by_doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('test_category', sa.String(100), nullable=False),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('ORDERED', 'SAMPLE_COLLECTED', 'IN_ANALYSIS', 'COMPLETED', 'CANCELLED', name='lab_order_status_enum'),
            nullable=False,
            server_default='ORDERED',
        ),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_lab_orders_consultation_id', 'lab_orders', ['consultation_id'])
    op.create_index('ix_lab_orders_patient_id', 'lab_orders', ['patient_id'])
    op.create_index('ix_lab_orders_facility_id', 'lab_orders', ['facility_id'])

    # 8. Lab Results
    op.create_table(
        'lab_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lab_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lab_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('test_name', sa.String(255), nullable=False),
        sa.Column('result_value', sa.String(255), nullable=False),
        sa.Column('reference_range', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('is_abnormal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('performed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_lab_results_lab_order_id', 'lab_results', ['lab_order_id'])

    # 9. Referrals
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('to_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('to_facility_name', sa.String(255), nullable=False),
        sa.Column('referral_reason', sa.Text(), nullable=False),
        sa.Column(
            'urgency',
            sa.Enum('ROUTINE', 'URGENT', 'EMERGENCY', name='referral_urgency_enum'),
            nullable=False,
            server_default='ROUTINE',
        ),
        sa.Column('clinical_summary', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'ACCEPTED', 'COMPLETED', 'REJECTED', name='referral_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column('referred_by_doctor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_referrals_consultation_id', 'referrals', ['consultation_id'])
    op.create_index('ix_referrals_patient_id', 'referrals', ['patient_id'])
    op.create_index('ix_referrals_from_facility_id', 'referrals', ['from_facility_id'])


def downgrade() -> None:
    op.drop_table('referrals')
    op.drop_table('lab_results')
    op.drop_table('lab_orders')
    op.drop_table('prescription_items')
    op.drop_table('prescriptions')
    op.drop_table('diagnoses')
    op.drop_table('consultations')
    op.drop_table('appointments')
    op.drop_table('patients')
    sa.Enum(name='referral_status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='referral_urgency_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='lab_order_status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='prescription_item_status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='prescription_status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='diagnosis_type_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='consultation_status_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='appointment_status_enum').drop(op.get_bind(), checkfirst=False)
