# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""remove_opensearch_and_add_solr

Revision ID: 27f8c9b4ed05
Revises: d092604db5a9
Create Date: 2026-06-08 13:19:08.410201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '27f8c9b4ed05'
down_revision: Union[str, Sequence[str], None] = 'd092604db5a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop constraint from mw_ranger_platform linking opensearch_id
    op.drop_constraint(op.f('mw_ranger_platform_opensearch_id_fkey'), 'mw_ranger_platform', type_='foreignkey')
    op.drop_column('mw_ranger_platform', 'opensearch_id')

    # Add solr_id to mw_ranger_platform
    op.add_column('mw_ranger_platform', sa.Column('solr_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('mw_ranger_platform_solr_id_fkey'), 'mw_ranger_platform', 'mw_solr_platform', ['solr_id'], ['id'])

    # Drop tables: mw_opensearch_platform_state, mw_opensearch_platform
    op.drop_index(op.f('ix_mw_opensearch_platform_state_status'), table_name='mw_opensearch_platform_state')
    op.drop_index(op.f('ix_mw_opensearch_platform_state_platform_id'), table_name='mw_opensearch_platform_state')
    op.drop_table('mw_opensearch_platform_state')
    op.drop_index(op.f('ix_mw_opensearch_platform_project_id'), table_name='mw_opensearch_platform')
    op.drop_table('mw_opensearch_platform')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-create tables: mw_opensearch_platform, mw_opensearch_platform_state
    op.create_table('mw_opensearch_platform',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('replica_count', sa.Integer(), nullable=False),
    sa.Column('chart_version', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('override_image', sa.Boolean(), nullable=False),
    sa.Column('image', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('image_tag', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('storage_size', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('cpu_request', sa.Float(), nullable=False),
    sa.Column('cpu_limit', sa.Float(), nullable=False),
    sa.Column('mem_request', sa.Float(), nullable=False),
    sa.Column('mem_limit', sa.Float(), nullable=False),
    sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('additional_properties', sqlalchemy_utils.types.json.JSONType(), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['mw_project.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_mw_opensearch_platform_project_id'), 'mw_opensearch_platform', ['project_id'], unique=False)
    
    op.create_table('mw_opensearch_platform_state',
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
    sa.Column('opensearch_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('opensearch_url_ipv6', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('admin_password', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['platform_id'], ['mw_opensearch_platform.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mw_opensearch_platform_state_platform_id'), 'mw_opensearch_platform_state', ['platform_id'], unique=False)
    op.create_index(op.f('ix_mw_opensearch_platform_state_status'), 'mw_opensearch_platform_state', ['status'], unique=False)

    # Swap columns on mw_ranger_platform
    op.drop_constraint(op.f('mw_ranger_platform_solr_id_fkey'), 'mw_ranger_platform', type_='foreignkey')
    op.drop_column('mw_ranger_platform', 'solr_id')
    op.add_column('mw_ranger_platform', sa.Column('opensearch_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('mw_ranger_platform_opensearch_id_fkey'), 'mw_ranger_platform', 'mw_opensearch_platform', ['opensearch_id'], ['id'])

