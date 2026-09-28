"""Phase 3 & 4: Pharmacy, Inventory, FEFO Dispensing, and Supply Chain Transfers

Revision ID: a1b2c3d4e5f6
Revises: f8b3c9d12a45
Create Date: 2026-09-27 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f8b3c9d12a45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Enums
    batch_status_enum = postgresql.ENUM(
        'AVAILABLE', 'QUARANTINED', 'EXPIRED', 'DEPLETED', 'DAMAGED', 'RECALLED',
        name='batch_status_enum',
        create_type=True
    )
    batch_status_enum.create(op.get_bind(), checkfirst=True)

    stock_movement_type_enum = postgresql.ENUM(
        'RECEIPT', 'DISPENSE', 'TRANSFER_OUT', 'TRANSFER_IN', 'ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN',
        name='stock_movement_type_enum',
        create_type=True
    )
    stock_movement_type_enum.create(op.get_bind(), checkfirst=True)

    stock_transfer_status_enum = postgresql.ENUM(
        'REQUESTED', 'APPROVED', 'DISPATCHED', 'IN_TRANSIT', 'RECEIVED', 'REJECTED', 'CANCELLED',
        name='stock_transfer_status_enum',
        create_type=True
    )
    stock_transfer_status_enum.create(op.get_bind(), checkfirst=True)

    shortage_severity_enum = postgresql.ENUM(
        'LOW', 'MEDIUM', 'HIGH', 'CRITICAL',
        name='shortage_severity_enum',
        create_type=True
    )
    shortage_severity_enum.create(op.get_bind(), checkfirst=True)

    shortage_status_enum = postgresql.ENUM(
        'REPORTED', 'INVESTIGATING', 'ACTION_TAKEN', 'RESOLVED', 'DISMISSED',
        name='shortage_status_enum',
        create_type=True
    )
    shortage_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Table: inventory_items
    op.create_table(
        'inventory_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_reserved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_level', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('minimum_stock_level', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('maximum_stock_level', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('unit_cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('quantity_on_hand >= 0', name='ck_inventory_items_non_negative_on_hand'),
        sa.CheckConstraint('quantity_reserved >= 0', name='ck_inventory_items_non_negative_reserved'),
        sa.UniqueConstraint('facility_id', 'medication_id', name='uq_inventory_items_facility_medication'),
    )
    op.create_index('ix_inventory_items_facility_id', 'inventory_items', ['facility_id'])
    op.create_index('ix_inventory_items_medication_id', 'inventory_items', ['medication_id'])

    # 3. Table: inventory_batches
    op.create_table(
        'inventory_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_number', sa.String(100), nullable=False),
        sa.Column('manufacture_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=False),
        sa.Column('initial_quantity', sa.Integer(), nullable=False),
        sa.Column('current_quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('AVAILABLE', 'QUARANTINED', 'EXPIRED', 'DEPLETED', 'DAMAGED', 'RECALLED', name='batch_status_enum'), nullable=False, server_default='AVAILABLE'),
        sa.Column('supplier_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('current_quantity >= 0', name='ck_inventory_batches_non_negative_current'),
        sa.CheckConstraint('initial_quantity > 0', name='ck_inventory_batches_positive_initial'),
        sa.UniqueConstraint('inventory_item_id', 'batch_number', name='uq_inventory_batches_item_batch_no'),
    )
    op.create_index('ix_inventory_batches_inventory_item_id', 'inventory_batches', ['inventory_item_id'])
    op.create_index('ix_inventory_batches_expiry_date', 'inventory_batches', ['expiry_date'])
    op.create_index('ix_inventory_batches_status', 'inventory_batches', ['status'])

    # 4. Table: stock_movements
    op.create_table(
        'stock_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inventory_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('movement_type', sa.Enum('RECEIPT', 'DISPENSE', 'TRANSFER_OUT', 'TRANSFER_IN', 'ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN', name='stock_movement_type_enum'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('reference_id', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('quantity != 0', name='ck_stock_movements_non_zero_qty'),
    )
    op.create_index('ix_stock_movements_facility_id', 'stock_movements', ['facility_id'])
    op.create_index('ix_stock_movements_inventory_item_id', 'stock_movements', ['inventory_item_id'])
    op.create_index('ix_stock_movements_created_at', 'stock_movements', ['created_at'])

    # 5. Table: dispensing_records
    op.create_table(
        'dispensing_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prescription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prescriptions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prescription_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prescription_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('dispensed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity_dispensed', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('quantity_dispensed > 0', name='ck_dispensing_records_positive_qty'),
    )
    op.create_index('ix_dispensing_records_prescription_id', 'dispensing_records', ['prescription_id'])
    op.create_index('ix_dispensing_records_facility_id', 'dispensing_records', ['facility_id'])

    # 6. Table: dispensing_allocations
    op.create_table(
        'dispensing_allocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dispensing_record_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dispensing_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_batches.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('allocated_quantity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('allocated_quantity > 0', name='ck_dispensing_allocations_positive_qty'),
    )
    op.create_index('ix_dispensing_allocations_record_id', 'dispensing_allocations', ['dispensing_record_id'])
    op.create_index('ix_dispensing_allocations_batch_id', 'dispensing_allocations', ['batch_id'])

    # 7. Table: stock_transfers
    op.create_table(
        'stock_transfers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transfer_number', sa.String(50), nullable=False, unique=True),
        sa.Column('source_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('destination_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('inventory_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('requested_quantity', sa.Integer(), nullable=False),
        sa.Column('dispatched_quantity', sa.Integer(), nullable=True),
        sa.Column('received_quantity', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('REQUESTED', 'APPROVED', 'DISPATCHED', 'IN_TRANSIT', 'RECEIVED', 'REJECTED', 'CANCELLED', name='stock_transfer_status_enum'), nullable=False, server_default='REQUESTED'),
        sa.Column('requested_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('dispatched_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('received_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.CheckConstraint('requested_quantity > 0', name='ck_stock_transfers_positive_requested'),
    )
    op.create_index('ix_stock_transfers_source_facility_id', 'stock_transfers', ['source_facility_id'])
    op.create_index('ix_stock_transfers_destination_facility_id', 'stock_transfers', ['destination_facility_id'])
    op.create_index('ix_stock_transfers_status', 'stock_transfers', ['status'])

    # 8. Table: shortage_incidents
    op.create_table(
        'shortage_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_number', sa.String(50), nullable=False, unique=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='shortage_severity_enum'), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.Enum('REPORTED', 'INVESTIGATING', 'ACTION_TAKEN', 'RESOLVED', 'DISMISSED', name='shortage_status_enum'), nullable=False, server_default='REPORTED'),
        sa.Column('reported_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('estimated_impact_patients', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_shortage_incidents_facility_id', 'shortage_incidents', ['facility_id'])
    op.create_index('ix_shortage_incidents_status', 'shortage_incidents', ['status'])


def downgrade() -> None:
    op.drop_table('shortage_incidents')
    op.drop_table('stock_transfers')
    op.drop_table('dispensing_allocations')
    op.drop_table('dispensing_records')
    op.drop_table('stock_movements')
    op.drop_table('inventory_batches')
    op.drop_table('inventory_items')

    shortage_status_enum = postgresql.ENUM('REPORTED', 'INVESTIGATING', 'ACTION_TAKEN', 'RESOLVED', 'DISMISSED', name='shortage_status_enum')
    shortage_status_enum.drop(op.get_bind(), checkfirst=True)

    shortage_severity_enum = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='shortage_severity_enum')
    shortage_severity_enum.drop(op.get_bind(), checkfirst=True)

    stock_transfer_status_enum = postgresql.ENUM('REQUESTED', 'APPROVED', 'DISPATCHED', 'IN_TRANSIT', 'RECEIVED', 'REJECTED', 'CANCELLED', name='stock_transfer_status_enum')
    stock_transfer_status_enum.drop(op.get_bind(), checkfirst=True)

    stock_movement_type_enum = postgresql.ENUM('RECEIPT', 'DISPENSE', 'TRANSFER_OUT', 'TRANSFER_IN', 'ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN', name='stock_movement_type_enum')
    stock_movement_type_enum.drop(op.get_bind(), checkfirst=True)

    batch_status_enum = postgresql.ENUM('AVAILABLE', 'QUARANTINED', 'EXPIRED', 'DEPLETED', 'DAMAGED', 'RECALLED', name='batch_status_enum')
    batch_status_enum.drop(op.get_bind(), checkfirst=True)
