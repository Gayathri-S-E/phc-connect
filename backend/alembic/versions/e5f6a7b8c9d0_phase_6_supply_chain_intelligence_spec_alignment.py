"""Phase 6: Supply chain logistics, intelligence tables, and DATABASE.md spec alignment

Merges the two existing heads (a1b2c3d4e5f6, d2e3f4a5b6c7).

Revision ID: e5f6a7b8c9d0
Revises: a1b2c3d4e5f6, d2e3f4a5b6c7
Create Date: 2026-09-28 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'd2e3f4a5b6c7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUMS = {
    'warehouse_storage_type_enum': ('AMBIENT', 'COLD_CHAIN', 'HAZARDOUS'),
    'purchase_request_status_enum': ('SUBMITTED', 'DISTRICT_APPROVED', 'REJECTED', 'CONVERTED_TO_PO'),
    'purchase_request_urgency_enum': ('ROUTINE', 'URGENT', 'EMERGENCY'),
    'purchase_order_status_enum': ('DRAFT', 'ISSUED', 'ACKNOWLEDGED', 'IN_TRANSIT', 'FULFILLED', 'CANCELLED'),
    'shipment_status_enum': ('PENDING', 'DISPATCHED', 'IN_TRANSIT', 'DELAYED', 'DELIVERED', 'CANCELLED'),
    'shipment_event_type_enum': ('DEPARTED', 'MILESTONE_CHECKPOINT', 'TEMPERATURE_EXCURSION', 'DELAY_REPORTED', 'DELIVERED'),
    'alert_type_enum': ('LOW_STOCK', 'CRITICAL_SHORTAGE', 'BATCH_EXPIRING', 'COLD_CHAIN_BREACH', 'ABNORMAL_DEMAND'),
    'alert_severity_enum': ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY'),
    'stock_movement_reference_type_enum': ('PRESCRIPTION', 'TRANSFER', 'PO', 'ADJUSTMENT'),
    'transfer_urgency_enum': ('NORMAL', 'EMERGENCY_SHORTAGE'),
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*ENUMS[name], name=name, create_type=False)


def _uuid_pk() -> sa.Column:
    return sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'))


def _timestamps() -> list:
    return [
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in ENUMS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.execute("ALTER TYPE shortage_status_enum ADD VALUE IF NOT EXISTS 'ESCALATED_DISTRICT'")
    op.execute("ALTER TYPE shortage_status_enum ADD VALUE IF NOT EXISTS 'ESCALATED_STATE'")

    # --- Supply chain ---
    op.create_table(
        'suppliers',
        _uuid_pk(),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('license_number', sa.String(100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('reliability_score', sa.Numeric(3, 2), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index('ix_suppliers_code', 'suppliers', ['code'])

    op.create_table(
        'warehouses',
        _uuid_pk(),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('storage_type', _enum('warehouse_storage_type_enum'), nullable=False, server_default='AMBIENT'),
        sa.Column('total_sqft', sa.Integer(), nullable=True),
        sa.Column('utilized_capacity_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
    )
    op.create_index('ix_warehouses_facility_id', 'warehouses', ['facility_id'])
    op.create_index('ix_warehouses_code', 'warehouses', ['code'])

    op.create_table(
        'purchase_requests',
        _uuid_pk(),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', _enum('purchase_request_status_enum'), nullable=False, server_default='SUBMITTED'),
        sa.Column('urgency', _enum('purchase_request_urgency_enum'), nullable=False, server_default='ROUTINE'),
        sa.Column('total_estimated_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        *_timestamps(),
    )
    op.create_index('ix_purchase_requests_facility_id', 'purchase_requests', ['facility_id'])

    op.create_table(
        'purchase_orders',
        _uuid_pk(),
        sa.Column('po_number', sa.String(50), nullable=False, unique=True),
        sa.Column('purchase_request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_requests.id', ondelete='SET NULL'), nullable=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('destination_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', _enum('purchase_order_status_enum'), nullable=False, server_default='DRAFT'),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        *_timestamps(),
    )
    op.create_index('ix_purchase_orders_po_number', 'purchase_orders', ['po_number'])
    op.create_index('ix_purchase_orders_purchase_request_id', 'purchase_orders', ['purchase_request_id'])
    op.create_index('ix_purchase_orders_supplier_id', 'purchase_orders', ['supplier_id'])
    op.create_index('ix_purchase_orders_destination_facility_id', 'purchase_orders', ['destination_facility_id'])

    op.create_table(
        'shipments',
        _uuid_pk(),
        sa.Column('tracking_number', sa.String(100), nullable=False, unique=True),
        sa.Column('purchase_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('purchase_orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('transfer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stock_transfers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('origin_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('destination_facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', _enum('shipment_status_enum'), nullable=False, server_default='PENDING'),
        sa.Column('carrier_name', sa.String(255), nullable=True),
        sa.Column('temperature_monitored', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint('purchase_order_id IS NOT NULL OR transfer_id IS NOT NULL', name='ck_shipments_has_source'),
    )
    op.create_index('ix_shipments_tracking_number', 'shipments', ['tracking_number'])
    op.create_index('ix_shipments_purchase_order_id', 'shipments', ['purchase_order_id'])
    op.create_index('ix_shipments_transfer_id', 'shipments', ['transfer_id'])
    op.create_index('ix_shipments_destination_facility_id', 'shipments', ['destination_facility_id'])
    op.create_index('ix_shipments_dispatched_at', 'shipments', ['dispatched_at'])

    op.create_table(
        'shipment_events',
        _uuid_pk(),
        sa.Column('shipment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shipments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', _enum('shipment_event_type_enum'), nullable=False),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('latitude', sa.Numeric(9, 6), nullable=True),
        sa.Column('longitude', sa.Numeric(9, 6), nullable=True),
        sa.Column('recorded_temp', sa.Numeric(5, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('logged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_shipment_events_shipment_id', 'shipment_events', ['shipment_id'])

    # --- Intelligence & operations ---
    op.create_table(
        'alerts',
        _uuid_pk(),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=True),
        sa.Column('alert_type', _enum('alert_type_enum'), nullable=False),
        sa.Column('severity', _enum('alert_severity_enum'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_acknowledged', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_alerts_facility_id', 'alerts', ['facility_id'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])

    op.create_table(
        'system_configs',
        _uuid_pk(),
        sa.Column('config_key', sa.String(255), nullable=False, unique=True),
        sa.Column('config_value', postgresql.JSONB(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_system_configs_config_key', 'system_configs', ['config_key'])

    op.create_table(
        'forecast_records',
        _uuid_pk(),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('medications.id', ondelete='CASCADE'), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('forecast_horizon_days', sa.Integer(), nullable=False),
        sa.Column('predicted_consumption', sa.Numeric(10, 2), nullable=False),
        sa.Column('confidence_interval_lower', sa.Numeric(10, 2), nullable=True),
        sa.Column('confidence_interval_upper', sa.Numeric(10, 2), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_forecast_records_facility_id', 'forecast_records', ['facility_id'])
    op.create_index('ix_forecast_records_medication_id', 'forecast_records', ['medication_id'])

    # --- Alignment of existing tables ---
    op.add_column('medications', sa.Column('code', sa.String(50), nullable=True))
    op.add_column('medications', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('medications', sa.Column('is_essential', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('medications', sa.Column('storage_temperature_min', sa.Numeric(5, 2), nullable=True))
    op.add_column('medications', sa.Column('storage_temperature_max', sa.Numeric(5, 2), nullable=True))
    op.create_index('ix_medications_code', 'medications', ['code'], unique=True)
    op.create_index('ix_medications_category', 'medications', ['category'])

    op.add_column('inventory_items', sa.Column('critical_level', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('inventory_items', sa.Column('max_capacity', sa.Integer(), nullable=True))
    op.execute('UPDATE inventory_items SET critical_level = LEAST(10, reorder_level)')
    op.create_check_constraint('ck_inventory_items_reorder_gte_critical', 'inventory_items', 'reorder_level >= critical_level')

    op.add_column('inventory_batches', sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True))
    op.add_column('inventory_batches', sa.Column('unit_cost', sa.Numeric(10, 2), nullable=True))
    op.create_index('ix_inventory_batches_supplier_id', 'inventory_batches', ['supplier_id'])
    op.create_index('ix_inventory_batches_item_expiry', 'inventory_batches', ['inventory_item_id', 'expiry_date'])

    op.add_column('stock_movements', sa.Column('reference_type', _enum('stock_movement_reference_type_enum'), nullable=True))
    op.add_column('stock_transfers', sa.Column('urgency', _enum('transfer_urgency_enum'), nullable=False, server_default='NORMAL'))

    op.create_check_constraint(
        'ck_prescription_items_dispensed_lte_prescribed',
        'prescription_items',
        'quantity_dispensed <= quantity_prescribed',
    )

    # Rows with non-IP values (e.g. proxy strings) can't be cast; drop them to NULL.
    op.execute("""
        DO $$
        DECLARE r record;
        BEGIN
            FOR r IN SELECT id, ip_address FROM user_sessions WHERE ip_address IS NOT NULL LOOP
                BEGIN
                    PERFORM r.ip_address::inet;
                EXCEPTION WHEN others THEN
                    UPDATE user_sessions SET ip_address = NULL WHERE id = r.id;
                END;
            END LOOP;
        END $$;
    """)
    op.alter_column(
        'user_sessions', 'ip_address',
        type_=postgresql.INET(),
        existing_type=sa.String(50),
        postgresql_using='ip_address::inet',
    )

    # DB-level UUID generation for every UUID primary key (models still default in Python for SQLite tests).
    op.execute("""
        DO $$
        DECLARE r record;
        BEGIN
            FOR r IN
                SELECT c.table_name
                FROM information_schema.columns c
                JOIN information_schema.table_constraints tc
                  ON tc.table_schema = c.table_schema AND tc.table_name = c.table_name AND tc.constraint_type = 'PRIMARY KEY'
                JOIN information_schema.key_column_usage k
                  ON k.constraint_name = tc.constraint_name AND k.table_schema = c.table_schema
                 AND k.table_name = c.table_name AND k.column_name = c.column_name
                WHERE c.table_schema = 'public' AND c.column_name = 'id' AND c.data_type = 'uuid'
            LOOP
                EXECUTE format('ALTER TABLE %I ALTER COLUMN id SET DEFAULT gen_random_uuid()', r.table_name);
            END LOOP;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        DECLARE r record;
        BEGIN
            FOR r IN
                SELECT table_name FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'id' AND data_type = 'uuid'
                  AND column_default = 'gen_random_uuid()'
            LOOP
                EXECUTE format('ALTER TABLE %I ALTER COLUMN id DROP DEFAULT', r.table_name);
            END LOOP;
        END $$;
    """)

    op.alter_column(
        'user_sessions', 'ip_address',
        type_=sa.String(50),
        existing_type=postgresql.INET(),
        postgresql_using='host(ip_address)',
    )

    op.drop_constraint('ck_prescription_items_dispensed_lte_prescribed', 'prescription_items', type_='check')
    op.drop_column('stock_transfers', 'urgency')
    op.drop_column('stock_movements', 'reference_type')

    op.drop_index('ix_inventory_batches_item_expiry', table_name='inventory_batches')
    op.drop_index('ix_inventory_batches_supplier_id', table_name='inventory_batches')
    op.drop_column('inventory_batches', 'unit_cost')
    op.drop_column('inventory_batches', 'supplier_id')

    op.drop_constraint('ck_inventory_items_reorder_gte_critical', 'inventory_items', type_='check')
    op.drop_column('inventory_items', 'max_capacity')
    op.drop_column('inventory_items', 'critical_level')

    op.drop_index('ix_medications_category', table_name='medications')
    op.drop_index('ix_medications_code', table_name='medications')
    for col in ('storage_temperature_max', 'storage_temperature_min', 'is_essential', 'category', 'code'):
        op.drop_column('medications', col)

    for table in (
        'forecast_records', 'system_configs', 'alerts',
        'shipment_events', 'shipments', 'purchase_orders', 'purchase_requests',
        'warehouses', 'suppliers',
    ):
        op.drop_table(table)

    bind = op.get_bind()
    for name, values in ENUMS.items():
        postgresql.ENUM(*values, name=name).drop(bind, checkfirst=True)
