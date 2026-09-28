"""Phase 2.1: Vitals, Clinical Amendments, Medications, and Diagnosis Codes

Revision ID: 93a1c4b72ef1
Revises: 61cd8b486dbf
Create Date: 2026-09-27 21:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '93a1c4b72ef1'
down_revision: Union[str, None] = '61cd8b486dbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Medications Master Catalog Table
    op.create_table(
        'medications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('generic_name', sa.String(255), nullable=False),
        sa.Column('brand_name', sa.String(255), nullable=True),
        sa.Column('strength', sa.String(100), nullable=False),
        sa.Column('dosage_form', sa.String(100), nullable=False),
        sa.Column('route', sa.String(100), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_medications_generic_name', 'medications', ['generic_name'])

    # 2. Diagnosis Codes Reference Table (ICD-10)
    op.create_table(
        'diagnosis_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, server_default='ICD-10'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_diagnosis_codes_code', 'diagnosis_codes', ['code'])
    op.create_index('ix_diagnosis_codes_category', 'diagnosis_codes', ['category'])

    # 3. Dedicated Vitals Table
    op.create_table(
        'vitals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('systolic_bp', sa.Integer(), nullable=True),
        sa.Column('diastolic_bp', sa.Integer(), nullable=True),
        sa.Column('pulse_rate', sa.Integer(), nullable=True),
        sa.Column('temperature_celsius', sa.Float(), nullable=True),
        sa.Column('respiratory_rate', sa.Integer(), nullable=True),
        sa.Column('spo2_percent', sa.Integer(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('recorded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_vitals_consultation_id', 'vitals', ['consultation_id'])
    op.create_index('ix_vitals_recorded_by_id', 'vitals', ['recorded_by_id'])

    # 4. Clinical Amendments Table (Immutability & Addenda)
    op.create_table(
        'clinical_amendments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('consultations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amendment_reason', sa.Text(), nullable=False),
        sa.Column('amendment_notes', sa.Text(), nullable=False),
        sa.Column('amended_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_clinical_amendments_consultation_id', 'clinical_amendments', ['consultation_id'])
    op.create_index('ix_clinical_amendments_amended_by_id', 'clinical_amendments', ['amended_by_id'])

    # 5. Link PrescriptionItem to Medication catalog
    op.add_column('prescription_items', sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_prescription_items_medication_id', 'prescription_items', ['medication_id'])


def downgrade() -> None:
    op.drop_index('ix_prescription_items_medication_id', table_name='prescription_items')
    op.drop_column('prescription_items', 'medication_id')

    op.drop_index('ix_clinical_amendments_amended_by_id', table_name='clinical_amendments')
    op.drop_index('ix_clinical_amendments_consultation_id', table_name='clinical_amendments')
    op.drop_table('clinical_amendments')

    op.drop_index('ix_vitals_recorded_by_id', table_name='vitals')
    op.drop_index('ix_vitals_consultation_id', table_name='vitals')
    op.drop_table('vitals')

    op.drop_index('ix_diagnosis_codes_category', table_name='diagnosis_codes')
    op.drop_index('ix_diagnosis_codes_code', table_name='diagnosis_codes')
    op.drop_table('diagnosis_codes')

    op.drop_index('ix_medications_generic_name', table_name='medications')
    op.drop_table('medications')
