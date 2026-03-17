"""consolidated superset and ldap

Revision ID: d8959af48e47
Revises: 997ede4dadde
Create Date: 2026-03-17 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'd8959af48e47'
down_revision: Union[str, Sequence[str], None] = '997ede4dadde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create mw_superset_platform
    op.create_table('mw_superset_platform',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('chart_version', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('superset_secret_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('platform_pgsql_id', sa.Integer(), nullable=False),
        sa.Column('ldap_config_id', sa.Integer(), nullable=True),
        sa.Column('database_source_ids', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('trino_ids', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('cpu_request', sa.Float(), nullable=False),
        sa.Column('cpu_limit', sa.Float(), nullable=False),
        sa.Column('mem_request', sa.Float(), nullable=False),
        sa.Column('mem_limit', sa.Float(), nullable=False),
        sa.Column('override_image', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('image', sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default='ghcr.io/kagesenshi/mindweaver/superset:latest'),
        sa.Column('auth_role_mapping', sqlalchemy_utils.types.json.JSONType(), nullable=False, server_default='[]'),
        sa.ForeignKeyConstraint(['ldap_config_id'], ['mw_ldap_config.id'], ),
        sa.ForeignKeyConstraint(['platform_pgsql_id'], ['mw_pgsql_platform.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['mw_project.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_mw_superset_platform_project_id'), 'mw_superset_platform', ['project_id'], unique=False)

    # Create mw_superset_platform_state
    op.create_table('mw_superset_platform_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column('created', sa.DateTime(timezone=True), nullable=False),
        sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('message', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('node_ports', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('cluster_nodes', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('extra_data', sqlalchemy_utils.types.json.JSONType(), nullable=False),
        sa.Column('superset_uri', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('superset_uri_ipv6', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('admin_user', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(['platform_id'], ['mw_superset_platform.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mw_superset_platform_state_platform_id'), 'mw_superset_platform_state', ['platform_id'], unique=False)
    op.create_index(op.f('ix_mw_superset_platform_state_status'), 'mw_superset_platform_state', ['status'], unique=False)

    # Add ldap user group attr
    op.add_column('mw_ldap_config', sa.Column('user_group_attr', sqlmodel.sql.sqltypes.AutoString(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mw_ldap_config', 'user_group_attr')
    op.drop_index(op.f('ix_mw_superset_platform_state_status'), table_name='mw_superset_platform_state')
    op.drop_index(op.f('ix_mw_superset_platform_state_platform_id'), table_name='mw_superset_platform_state')
    op.drop_table('mw_superset_platform_state')
    op.drop_index(op.f('ix_mw_superset_platform_project_id'), table_name='mw_superset_platform')
    op.drop_table('mw_superset_platform')
