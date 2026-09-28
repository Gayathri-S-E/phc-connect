"""Phase 4: Lab Samples, Accessioning and Critical Alerts

Revision ID: c1d2e3f4a5b6
Revises: f8b3c9d12a45
Create Date: 2026-09-27 22:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'f8b3c9d12a45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add sample collection columns to lab_orders
    op.add_column('lab_orders', sa.Column('sample_type', sa.String(100), nullable=True))
    op.add_column('lab_orders', sa.Column('sample_barcode', sa.String(100), nullable=True))
    op.add_column('lab_orders', sa.Column('sample_collected_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Add critical_alert column to lab_results
    op.add_column('lab_results', sa.Column('critical_alert', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('lab_results', 'critical_alert')
    op.drop_column('lab_orders', 'sample_collected_at')
    op.drop_column('lab_orders', 'sample_barcode')
    op.drop_column('lab_orders', 'sample_type')
