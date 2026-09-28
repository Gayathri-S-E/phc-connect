"""Initial schema: Identity, RBAC, Organizations, Facilities, Audit

Revision ID: 74749546cd8b
Revises: 
Create Date: 2026-09-27 20:13:42.654281

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '74749546cd8b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column(
            'org_type',
            sa.Enum('MINISTRY', 'STATE_HEALTH_DEPT', 'DISTRICT_HEALTH_OFFICE', 'VENDOR', name='organization_type_enum'),
            nullable=False,
            server_default='DISTRICT_HEALTH_OFFICE',
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_organizations_code', 'organizations', ['code'])

    # 2. Facilities
    op.create_table(
        'facilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column(
            'facility_type',
            sa.Enum('PHC', 'CHC', 'DISTRICT_HOSPITAL', 'CENTRAL_WAREHOUSE', 'DISTRICT_WAREHOUSE', name='facility_type_enum'),
            nullable=False,
            server_default='PHC',
        ),
        sa.Column('state', sa.String(100), nullable=False),
        sa.Column('district', sa.String(100), nullable=False),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_facilities_code', 'facilities', ['code'])
    op.create_index('ix_facilities_organization_id', 'facilities', ['organization_id'])
    op.create_index('ix_facilities_state', 'facilities', ['state'])
    op.create_index('ix_facilities_district', 'facilities', ['district'])

    # 3. Permissions
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_permissions_code', 'permissions', ['code'])
    op.create_index('ix_permissions_module', 'permissions', ['module'])

    # 4. Roles
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_roles_code', 'roles', ['code'])

    # 5. Role Permissions
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )

    # 6. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])
    op.create_index('ix_users_facility_id', 'users', ['facility_id'])

    # 7. User Roles
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='CASCADE'), nullable=True),
        sa.Column(
            'scope_level',
            sa.Enum('GLOBAL', 'STATE', 'DISTRICT', 'FACILITY', 'SELF', name='scope_level_enum'),
            nullable=False,
            server_default='FACILITY',
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])

    # 8. User Sessions
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_user_sessions_refresh_token_hash', 'user_sessions', ['refresh_token_hash'])

    # 9. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facilities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('old_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp()),
    )
    op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('user_sessions')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('facilities')
    op.drop_table('organizations')
    sa.Enum(name='scope_level_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='facility_type_enum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='organization_type_enum').drop(op.get_bind(), checkfirst=False)
